"""Deterministic machine-readable and visual Module B outputs."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sylvapapers_contracts import SensorRecord

from .service import MaintenanceAnalysisResult

plt.style.use("ggplot")

EXPORT_SCHEMA_VERSION = "1.0.0"


def _csv_safe(value: object) -> object:
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def _plot_sensor_anomalies(result: MaintenanceAnalysisResult, target: Path) -> None:
    by_machine: dict[str, list[SensorRecord]] = defaultdict(list)
    for record in result.sensor_records:
        by_machine[record.machine_id].append(record)
    assessment_by_machine = {item.machine_id: item for item in result.assessments}
    figure, axis = plt.subplots(figsize=(11, 6))
    for machine_id in sorted(by_machine):
        assessment = assessment_by_machine.get(machine_id)
        if assessment is None:
            continue
        importance = assessment.anomaly.variable_importance
        variable = max(importance, key=lambda name: importance[name]) if importance else None
        if variable is None:
            continue
        records = sorted(by_machine[machine_id], key=lambda item: item.timestamp)
        points = [
            (item.timestamp, item.values[variable]) for item in records if variable in item.values
        ]
        if not points:
            continue
        first = points[0][1]
        scale = max(max(abs(value - first) for _, value in points), 1e-9)
        time_hours = [(time - points[0][0]).total_seconds() / 3600 for time, _ in points]
        axis.plot(
            time_hours,
            [(value - first) / scale for _, value in points],
            label=f"{machine_id}: {variable}",
            linewidth=1.2,
        )
        if assessment.anomaly.is_anomaly:
            axis.scatter(
                time_hours[-1],
                (points[-1][1] - first) / scale,
                color="red",
                zorder=3,
            )
    axis.axhline(0, color="black", linewidth=0.6)
    axis.set_title("Évolution normalisée des capteurs et dernière anomalie EWMA")
    axis.set_ylabel("Écart normalisé au premier point")
    axis.set_xlabel("Heures depuis la première mesure")
    if len(by_machine) <= 12:
        axis.legend(fontsize=7, loc="best")
    figure.tight_layout()
    figure.savefig(target, dpi=150)
    plt.close(figure)


def _plot_risk_rul(result: MaintenanceAnalysisResult, target: Path) -> None:
    machines = [item.machine_id for item in result.assessments]
    risks = [item.reliability.failure_probability for item in result.assessments]
    ruls = [item.reliability.rul_hours for item in result.assessments]
    lower = [item.reliability.rul_lower_hours for item in result.assessments]
    upper = [item.reliability.rul_upper_hours for item in result.assessments]
    figure, (risk_axis, rul_axis) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    risk_axis.bar(machines, risks, color="#c45a3c")
    risk_axis.set_ylim(0, 1)
    risk_axis.set_ylabel("Probabilité de panne")
    risk_axis.set_title("Risque Weibull conditionnel sur l'horizon de prédiction")
    rul_axis.errorbar(
        machines,
        ruls,
        yerr=[
            [value - low for value, low in zip(ruls, lower, strict=True)],
            [high - value for value, high in zip(ruls, upper, strict=True)],
        ],
        fmt="o",
        color="#315b7d",
        capsize=3,
    )
    rul_axis.set_ylabel("RUL (heures de fonctionnement)")
    rul_axis.set_title("Durée de vie résiduelle médiane et intervalle d'incertitude")
    rul_axis.tick_params(axis="x", rotation=45, labelsize=8)
    figure.tight_layout()
    figure.savefig(target, dpi=150)
    plt.close(figure)


def _plot_policy_costs(result: MaintenanceAnalysisResult, target: Path) -> None:
    machines = [item.machine_id for item in result.assessments]
    policies = ("corrective", "preventive", "predictive")
    width = 0.25
    positions = list(range(len(machines)))
    figure, axis = plt.subplots(figsize=(11, 6))
    for offset, policy in enumerate(policies):
        costs = [
            next(row.expected_cost for row in item.policy_comparison if row.policy == policy)
            for item in result.assessments
        ]
        axis.bar(
            [position + (offset - 1) * width for position in positions],
            costs,
            width=width,
            label=policy,
        )
    axis.set_xticks(positions, machines, rotation=45, ha="right", fontsize=8)
    axis.set_ylabel(f"Coût attendu ({result.config.economics.currency})")
    axis.set_title("Comparaison des politiques corrective, préventive et prédictive")
    axis.legend()
    figure.tight_layout()
    figure.savefig(target, dpi=150)
    plt.close(figure)


def _plot_temporal_validation(result: MaintenanceAnalysisResult, target: Path) -> None:
    metrics = result.temporal_validation.metrics
    methods = [item.method.replace("_robust", "").upper() for item in metrics]
    precision = [item.precision or 0.0 for item in metrics]
    recall = [item.recall or 0.0 for item in metrics]
    f1_scores = [item.f1_score or 0.0 for item in metrics]
    positions = list(range(len(methods)))
    width = 0.24
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.bar([value - width for value in positions], precision, width, label="Précision")
    axis.bar(positions, recall, width, label="Rappel")
    axis.bar([value + width for value in positions], f1_scores, width, label="F1")
    axis.set_xticks(positions, methods)
    axis.set_ylim(0, 1)
    axis.set_ylabel("Score")
    axis.set_title("Backtesting temporel des alertes (fenêtres non censurées)")
    axis.legend()
    figure.tight_layout()
    figure.savefig(target, dpi=150)
    plt.close(figure)


def _plot_calibration(result: MaintenanceAnalysisResult, target: Path) -> None:
    bins = result.temporal_validation.calibration_bins
    figure, axis = plt.subplots(figsize=(6, 6))
    axis.plot([0, 1], [0, 1], linestyle="--", color="#666666", label="Idéal")
    if bins:
        axis.plot(
            [item.mean_predicted_probability for item in bins],
            [item.observed_failure_rate for item in bins],
            marker="o",
            color="#315b7d",
            label="Weibull observé",
        )
    else:
        axis.text(
            0.5,
            0.5,
            "Aucune fenêtre non censurée",
            ha="center",
            va="center",
            transform=axis.transAxes,
        )
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.set_xlabel("Probabilité prédite")
    axis.set_ylabel("Fréquence de panne observée")
    axis.set_title("Calibration temporelle du risque Weibull")
    axis.legend()
    figure.tight_layout()
    figure.savefig(target, dpi=150)
    plt.close(figure)


def _write_temporal_predictions(result: MaintenanceAnalysisResult, target: Path) -> None:
    fields = (
        "schema_version",
        "provenance",
        "data_classification",
        "machine_id",
        "assessed_at",
        "method",
        "anomaly_score",
        "anomaly_threshold",
        "is_alert",
        "failure_probability",
        "probability_unit",
        "horizon_hours",
        "horizon_unit",
        "observed_failure",
        "is_censored",
        "next_failure_at",
        "alert_lead_hours",
        "lead_time_unit",
        "observations_used",
    )
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in result.temporal_validation.predictions:
            writer.writerow(
                {
                    "schema_version": EXPORT_SCHEMA_VERSION,
                    "provenance": "module_b_temporal_backtest",
                    "data_classification": result.dataset.data_classification,
                    "machine_id": _csv_safe(item.machine_id),
                    "assessed_at": item.assessed_at.isoformat(),
                    "method": item.method,
                    "anomaly_score": round(item.anomaly_score, 9),
                    "anomaly_threshold": item.anomaly_threshold,
                    "is_alert": item.is_alert,
                    "failure_probability": round(item.failure_probability, 9),
                    "probability_unit": "ratio",
                    "horizon_hours": item.horizon_hours,
                    "horizon_unit": "operating_hour",
                    "observed_failure": (
                        "" if item.observed_failure is None else item.observed_failure
                    ),
                    "is_censored": item.is_censored,
                    "next_failure_at": (
                        item.next_failure_at.isoformat() if item.next_failure_at else ""
                    ),
                    "alert_lead_hours": (
                        round(item.alert_lead_hours, 6) if item.alert_lead_hours is not None else ""
                    ),
                    "lead_time_unit": "calendar_hour",
                    "observations_used": item.observations_used,
                }
            )


def _write_temporal_metrics(result: MaintenanceAnalysisResult, target: Path) -> None:
    fields = (
        "schema_version",
        "provenance",
        "data_classification",
        "method",
        "evaluated_points",
        "censored_points",
        "true_positive",
        "false_positive",
        "true_negative",
        "false_negative",
        "precision",
        "recall",
        "f1_score",
        "brier_score",
        "failure_events",
        "detected_failure_events",
        "missed_failure_events",
        "mean_alert_lead_hours",
        "median_alert_lead_hours",
        "lead_time_unit",
        "limitations",
    )
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in result.temporal_validation.metrics:
            writer.writerow(
                {
                    "schema_version": EXPORT_SCHEMA_VERSION,
                    "provenance": "module_b_temporal_backtest",
                    "data_classification": result.dataset.data_classification,
                    "method": item.method,
                    "evaluated_points": item.evaluated_points,
                    "censored_points": item.censored_points,
                    "true_positive": item.true_positive,
                    "false_positive": item.false_positive,
                    "true_negative": item.true_negative,
                    "false_negative": item.false_negative,
                    "precision": "" if item.precision is None else round(item.precision, 9),
                    "recall": "" if item.recall is None else round(item.recall, 9),
                    "f1_score": "" if item.f1_score is None else round(item.f1_score, 9),
                    "brier_score": ("" if item.brier_score is None else round(item.brier_score, 9)),
                    "failure_events": item.failure_events,
                    "detected_failure_events": item.detected_failure_events,
                    "missed_failure_events": item.missed_failure_events,
                    "mean_alert_lead_hours": (
                        ""
                        if item.mean_alert_lead_hours is None
                        else round(item.mean_alert_lead_hours, 6)
                    ),
                    "median_alert_lead_hours": (
                        ""
                        if item.median_alert_lead_hours is None
                        else round(item.median_alert_lead_hours, 6)
                    ),
                    "lead_time_unit": "calendar_hour",
                    "limitations": _csv_safe(" | ".join(item.limitations)),
                }
            )


def _write_calibration(result: MaintenanceAnalysisResult, target: Path) -> None:
    fields = (
        "schema_version",
        "provenance",
        "data_classification",
        "method",
        "bin_index",
        "probability_lower",
        "probability_upper",
        "sample_count",
        "mean_predicted_probability",
        "observed_failure_rate",
        "probability_unit",
    )
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in result.temporal_validation.calibration_bins:
            writer.writerow(
                {
                    "schema_version": EXPORT_SCHEMA_VERSION,
                    "provenance": "module_b_temporal_backtest",
                    "data_classification": result.dataset.data_classification,
                    "method": item.method,
                    "bin_index": item.bin_index,
                    "probability_lower": item.probability_lower,
                    "probability_upper": item.probability_upper,
                    "sample_count": item.sample_count,
                    "mean_predicted_probability": round(item.mean_predicted_probability, 9),
                    "observed_failure_rate": round(item.observed_failure_rate, 9),
                    "probability_unit": "ratio",
                }
            )


def _write_machine_features(result: MaintenanceAnalysisResult, target: Path) -> None:
    fields = (
        "schema_version",
        "provenance",
        "data_classification",
        "source_schema_version",
        "source_code_version",
        "assessment_id",
        "machine_id",
        "assessed_at",
        "risk_horizon_hours",
        "failure_probability",
        "probability_unit",
        "rul_hours",
        "rul_lower_hours",
        "rul_upper_hours",
        "time_unit",
        "anomaly_method",
        "anomaly_score",
        "is_anomaly",
        "recommended_policy",
        "urgency",
        "decision_confidence",
        "expected_cost",
        "currency",
        "expected_downtime_hours",
        "capacity_loss_ratio",
        "capacity_available_ratio",
        "ratio_unit",
        "assumptions_are_synthetic",
    )
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for assessment in result.assessments:
            selected = next(
                item
                for item in assessment.policy_comparison
                if item.policy == assessment.recommendation.policy
            )
            capacity_loss = min(
                1.0,
                selected.expected_downtime_hours / result.config.horizon_hours,
            )
            writer.writerow(
                {
                    "schema_version": EXPORT_SCHEMA_VERSION,
                    "provenance": "module_b_decision_features",
                    "data_classification": result.dataset.data_classification,
                    "source_schema_version": result.dataset.source_schema_version,
                    "source_code_version": result.dataset.source_code_version,
                    "assessment_id": _csv_safe(assessment.assessment_id),
                    "machine_id": _csv_safe(assessment.machine_id),
                    "assessed_at": assessment.created_at.isoformat(),
                    "risk_horizon_hours": assessment.reliability.horizon_hours,
                    "failure_probability": round(assessment.reliability.failure_probability, 9),
                    "probability_unit": "ratio",
                    "rul_hours": round(assessment.reliability.rul_hours, 6),
                    "rul_lower_hours": round(assessment.reliability.rul_lower_hours, 6),
                    "rul_upper_hours": round(assessment.reliability.rul_upper_hours, 6),
                    "time_unit": "operating_hour",
                    "anomaly_method": assessment.anomaly.method,
                    "anomaly_score": round(assessment.anomaly.score, 9),
                    "is_anomaly": assessment.anomaly.is_anomaly,
                    "recommended_policy": selected.policy,
                    "urgency": assessment.recommendation.urgency,
                    "decision_confidence": round(assessment.recommendation.confidence, 9),
                    "expected_cost": round(selected.expected_cost, 6),
                    "currency": selected.currency,
                    "expected_downtime_hours": round(selected.expected_downtime_hours, 6),
                    "capacity_loss_ratio": round(capacity_loss, 9),
                    "capacity_available_ratio": round(1 - capacity_loss, 9),
                    "ratio_unit": "ratio",
                    "assumptions_are_synthetic": (
                        selected.assumptions_are_synthetic
                        or "synthetic" in result.dataset.data_classification.lower()
                    ),
                }
            )


def save_maintenance_analysis(
    result: MaintenanceAnalysisResult,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Persist versioned contracts, flat interoperability tables and figures."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    assessments_path = destination / "maintenance_assessments.json"
    costs_path = destination / "maintenance_policy_costs.csv"
    sensor_figure = destination / "sensor_anomalies.png"
    reliability_figure = destination / "failure_risk_rul.png"
    policy_figure = destination / "maintenance_policy_costs.png"
    predictions_path = destination / "temporal_predictions.csv"
    metrics_path = destination / "temporal_validation_metrics.csv"
    calibration_path = destination / "probability_calibration.csv"
    features_path = destination / "machine_decision_features.csv"
    validation_path = destination / "temporal_validation.json"
    manifest_path = destination / "module_b_manifest.json"
    validation_figure = destination / "temporal_validation.png"
    calibration_figure = destination / "probability_calibration.png"

    assessments_path.write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.assessments],
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    with costs_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=(
                "schema_version",
                "provenance",
                "data_classification",
                "machine_id",
                "policy",
                "expected_cost",
                "currency",
                "expected_downtime_hours",
                "intervention_probability",
                "assumptions_are_synthetic",
            ),
        )
        writer.writeheader()
        for assessment in result.assessments:
            for policy in assessment.policy_comparison:
                writer.writerow(
                    {
                        "schema_version": EXPORT_SCHEMA_VERSION,
                        "provenance": "module_b_economic_comparison",
                        "data_classification": result.dataset.data_classification,
                        "machine_id": _csv_safe(assessment.machine_id),
                        "policy": policy.policy,
                        "expected_cost": round(policy.expected_cost, 6),
                        "currency": policy.currency,
                        "expected_downtime_hours": round(policy.expected_downtime_hours, 6),
                        "intervention_probability": round(policy.intervention_probability, 9),
                        "assumptions_are_synthetic": policy.assumptions_are_synthetic,
                    }
                )
    _write_temporal_predictions(result, predictions_path)
    _write_temporal_metrics(result, metrics_path)
    _write_calibration(result, calibration_path)
    _write_machine_features(result, features_path)
    validation_path.write_text(
        json.dumps(
            {
                "schema_version": EXPORT_SCHEMA_VERSION,
                "provenance": "module_b_temporal_backtest",
                "data_classification": result.dataset.data_classification,
                "predictions": [
                    item.model_dump(mode="json") for item in result.temporal_validation.predictions
                ],
                "metrics": [
                    item.model_dump(mode="json") for item in result.temporal_validation.metrics
                ],
                "calibration_bins": [
                    item.model_dump(mode="json")
                    for item in result.temporal_validation.calibration_bins
                ],
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    _plot_sensor_anomalies(result, sensor_figure)
    _plot_risk_rul(result, reliability_figure)
    _plot_policy_costs(result, policy_figure)
    _plot_temporal_validation(result, validation_figure)
    _plot_calibration(result, calibration_figure)
    flat_exports = {
        "policy_costs": costs_path.name,
        "temporal_predictions": predictions_path.name,
        "temporal_metrics": metrics_path.name,
        "probability_calibration": calibration_path.name,
        "machine_decision_features": features_path.name,
    }
    limitations = sorted(
        {
            limitation
            for metric in result.temporal_validation.metrics
            for limitation in metric.limitations
        }
    )
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": EXPORT_SCHEMA_VERSION,
                "provenance": "module_b",
                "data_classification": result.dataset.data_classification,
                "source_schema_version": result.dataset.source_schema_version,
                "source_code_version": result.dataset.source_code_version,
                "generated_at": datetime.now(UTC).isoformat(),
                "analysis_reference_at": max(
                    item.created_at for item in result.assessments
                ).isoformat(),
                "machine_count": len(result.assessments),
                "temporal_prediction_count": len(result.temporal_validation.predictions),
                "flat_exports": flat_exports,
                "json_contracts": {
                    "assessments": assessments_path.name,
                    "temporal_validation": validation_path.name,
                },
                "units": {
                    "probability": "ratio",
                    "time_to_failure": "operating_hour",
                    "alert_lead_time": "calendar_hour",
                    "capacity_impact": "ratio",
                    "cost": result.config.economics.currency,
                },
                "intended_consumers": ["module_c", "module_d", "module_e"],
                "limitations": limitations,
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "assessments": assessments_path,
        "policy_costs": costs_path,
        "sensor_anomalies_figure": sensor_figure,
        "failure_risk_rul_figure": reliability_figure,
        "policy_costs_figure": policy_figure,
        "temporal_predictions": predictions_path,
        "temporal_metrics": metrics_path,
        "probability_calibration": calibration_path,
        "machine_decision_features": features_path,
        "temporal_validation": validation_path,
        "manifest": manifest_path,
        "temporal_validation_figure": validation_figure,
        "probability_calibration_figure": calibration_figure,
    }
