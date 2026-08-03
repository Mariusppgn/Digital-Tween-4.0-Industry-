"""Leakage-free temporal validation for interpretable maintenance baselines."""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from sylvapapers_contracts import (
    MaintenanceAnalysisConfig,
    ProbabilityCalibrationBin,
    SensorRecord,
    TemporalPrediction,
    TemporalValidationMetrics,
)

from .anomaly import cusum_robust_anomaly, ewma_robust_anomaly
from .io import MaintenanceDataset
from .reliability import conditional_weibull_probability


@dataclass(frozen=True)
class TemporalValidationResult:
    """Detailed predictions, aggregate metrics and probability calibration."""

    predictions: list[TemporalPrediction]
    metrics: list[TemporalValidationMetrics]
    calibration_bins: list[ProbabilityCalibrationBin]


def _observation_end(dataset: MaintenanceDataset) -> datetime:
    timestamps = [record.timestamp for record in dataset.sensor_records]
    timestamps.extend(state.timestamp for state in dataset.machine_states)
    timestamps.extend(event.occurred_at for event in dataset.failure_events)
    timestamps.extend(
        intervention.completed_at for intervention in dataset.maintenance_interventions
    )
    if not timestamps:
        raise ValueError("temporal validation requires timestamped observations")
    return max(timestamps)


def _operating_age(
    record: SensorRecord,
    prefix: list[SensorRecord],
    dataset: MaintenanceDataset,
) -> float:
    if "operating_age_hours" in record.values:
        return max(0.0, record.values["operating_age_hours"])
    state_ages = [
        state.operating_age_hours
        for state in dataset.machine_states
        if state.machine_id == record.machine_id
        and state.timestamp <= record.timestamp
        and state.operating_age_hours is not None
    ]
    if state_ages:
        return max(state_ages)
    return max(0.0, (record.timestamp - prefix[0].timestamp).total_seconds() / 3_600)


def _predictions(
    dataset: MaintenanceDataset,
    config: MaintenanceAnalysisConfig,
) -> list[TemporalPrediction]:
    by_machine: dict[str, list[SensorRecord]] = defaultdict(list)
    for record in dataset.sensor_records:
        if record.quality != "bad" and record.machine_id not in config.excluded_machine_ids:
            by_machine[record.machine_id].append(record)
    end_at = _observation_end(dataset)
    horizon = timedelta(hours=config.horizon_hours)
    predictions: list[TemporalPrediction] = []
    for machine_id in sorted(by_machine):
        records = sorted(by_machine[machine_id], key=lambda item: (item.timestamp, item.sensor_id))
        if len(records) <= config.minimum_baseline_points:
            continue
        failures = sorted(
            event.occurred_at for event in dataset.failure_events if event.machine_id == machine_id
        )
        density = config.machine_failure_densities.get(machine_id, config.default_failure_density)
        for index in range(config.minimum_baseline_points, len(records)):
            prefix = records[: index + 1]
            assessed_at = prefix[-1].timestamp
            window_end = assessed_at + horizon
            next_failure = next(
                (when for when in failures if assessed_at < when <= window_end), None
            )
            is_censored = next_failure is None and window_end > end_at
            observed_failure = None if is_censored else next_failure is not None
            failure_probability = conditional_weibull_probability(
                _operating_age(prefix[-1], prefix, dataset),
                config.horizon_hours,
                density,
            )
            anomaly_results = (
                ewma_robust_anomaly(prefix, config),
                cusum_robust_anomaly(prefix, config),
            )
            for anomaly in anomaly_results:
                lead_hours = (
                    (next_failure - assessed_at).total_seconds() / 3_600
                    if anomaly.is_anomaly and next_failure is not None
                    else None
                )
                predictions.append(
                    TemporalPrediction(
                        machine_id=machine_id,
                        assessed_at=assessed_at,
                        method=anomaly.method,
                        anomaly_score=anomaly.score,
                        anomaly_threshold=anomaly.threshold,
                        is_alert=anomaly.is_anomaly,
                        failure_probability=failure_probability,
                        horizon_hours=config.horizon_hours,
                        observed_failure=observed_failure,
                        is_censored=is_censored,
                        next_failure_at=next_failure,
                        alert_lead_hours=lead_hours,
                        observations_used=len(prefix),
                        provenance="module_b_temporal_backtest",
                    )
                )
    return predictions


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _method_metrics(
    method: Literal["ewma_robust", "cusum_robust"],
    predictions: list[TemporalPrediction],
    dataset: MaintenanceDataset,
    config: MaintenanceAnalysisConfig,
) -> TemporalValidationMetrics:
    relevant = [item for item in predictions if item.method == method]
    evaluated = [item for item in relevant if not item.is_censored]
    true_positive = sum(item.is_alert and item.observed_failure is True for item in evaluated)
    false_positive = sum(item.is_alert and item.observed_failure is False for item in evaluated)
    true_negative = sum(not item.is_alert and item.observed_failure is False for item in evaluated)
    false_negative = sum(not item.is_alert and item.observed_failure is True for item in evaluated)
    precision = _safe_ratio(true_positive, true_positive + false_positive)
    recall = _safe_ratio(true_positive, true_positive + false_negative)
    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall > 0
        else None
    )
    brier_score = (
        sum(
            (item.failure_probability - float(item.observed_failure is True)) ** 2
            for item in evaluated
        )
        / len(evaluated)
        if evaluated
        else None
    )

    first_prediction_by_machine: dict[str, datetime] = {}
    for item in relevant:
        first_prediction_by_machine.setdefault(item.machine_id, item.assessed_at)
    failures = [
        event
        for event in dataset.failure_events
        if event.machine_id in first_prediction_by_machine
        and event.occurred_at >= first_prediction_by_machine[event.machine_id]
    ]
    event_leads: list[float] = []
    for failure in failures:
        eligible_alerts = [
            item
            for item in relevant
            if item.machine_id == failure.machine_id
            and item.is_alert
            and failure.occurred_at - timedelta(hours=config.horizon_hours)
            <= item.assessed_at
            < failure.occurred_at
        ]
        if eligible_alerts:
            earliest = min(item.assessed_at for item in eligible_alerts)
            event_leads.append((failure.occurred_at - earliest).total_seconds() / 3_600)

    limitations = [
        "Point-wise predictions overlap in time and are not statistically independent.",
    ]
    if len(evaluated) < 30:
        limitations.append(
            "Fewer than 30 uncensored points: precision and recall are descriptive only."
        )
    if not failures:
        limitations.append(
            "No evaluable failure event: event recall and alert lead time are not estimable."
        )
    censored_count = len(relevant) - len(evaluated)
    if censored_count:
        limitations.append(
            "Right-censored windows are excluded from confusion and calibration metrics."
        )
    return TemporalValidationMetrics(
        method=method,
        evaluated_points=len(evaluated),
        censored_points=censored_count,
        true_positive=true_positive,
        false_positive=false_positive,
        true_negative=true_negative,
        false_negative=false_negative,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        brier_score=brier_score,
        failure_events=len(failures),
        detected_failure_events=len(event_leads),
        missed_failure_events=len(failures) - len(event_leads),
        mean_alert_lead_hours=statistics.fmean(event_leads) if event_leads else None,
        median_alert_lead_hours=statistics.median(event_leads) if event_leads else None,
        limitations=limitations,
        provenance="module_b_temporal_backtest",
    )


def _calibration_bins(
    predictions: list[TemporalPrediction], bins: int
) -> list[ProbabilityCalibrationBin]:
    # EWMA and CUSUM rows share the same Weibull risk at a timestamp. Keeping
    # one method prevents double-counting the same outcome.
    evaluated = [
        item for item in predictions if item.method == "ewma_robust" and not item.is_censored
    ]
    grouped: dict[int, list[TemporalPrediction]] = defaultdict(list)
    for item in evaluated:
        index = min(int(item.failure_probability * bins), bins - 1)
        grouped[index].append(item)
    result: list[ProbabilityCalibrationBin] = []
    for index in sorted(grouped):
        rows = grouped[index]
        result.append(
            ProbabilityCalibrationBin(
                bin_index=index,
                probability_lower=index / bins,
                probability_upper=(index + 1) / bins,
                sample_count=len(rows),
                mean_predicted_probability=statistics.fmean(
                    item.failure_probability for item in rows
                ),
                observed_failure_rate=statistics.fmean(
                    float(item.observed_failure is True) for item in rows
                ),
                provenance="module_b_temporal_backtest",
            )
        )
    return result


def backtest_temporal_alerts(
    dataset: MaintenanceDataset,
    config: MaintenanceAnalysisConfig,
) -> TemporalValidationResult:
    """Backtest EWMA, CUSUM and Weibull risk with rolling origin prefixes.

    Each prediction sees only the sensor and state history available at its
    timestamp. Outcomes are looked up afterwards solely for evaluation.
    Windows without complete follow-up are marked as right-censored.
    """

    predictions = _predictions(dataset, config)
    metrics = [
        _method_metrics("ewma_robust", predictions, dataset, config),
        _method_metrics("cusum_robust", predictions, dataset, config),
    ]
    return TemporalValidationResult(
        predictions=predictions,
        metrics=metrics,
        calibration_bins=_calibration_bins(predictions, config.calibration_bins),
    )
