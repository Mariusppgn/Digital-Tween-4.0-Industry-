"""End-to-end maintenance analysis service linking Module A to Module B."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Literal

from sylvapapers_contracts import (
    FailureDensityConfig,
    MaintenanceAnalysisConfig,
    MaintenanceAssessment,
    MaintenanceRecommendation,
    SensorRecord,
)

from .anomaly import ewma_robust_anomaly
from .economics import compare_maintenance_policies
from .io import MaintenanceDataset, load_maintenance_config, load_module_a_outputs
from .reliability import estimate_reliability


@dataclass(frozen=True)
class MaintenanceAnalysisResult:
    """Complete deterministic Module B run, including source data for figures."""

    assessments: list[MaintenanceAssessment]
    sensor_records: list[SensorRecord]
    config: MaintenanceAnalysisConfig


def _latest_operating_age(machine_id: str, dataset: MaintenanceDataset) -> float:
    sensor_ages = [
        record.values["operating_age_hours"]
        for record in dataset.sensor_records
        if record.machine_id == machine_id and "operating_age_hours" in record.values
    ]
    if sensor_ages:
        return max(sensor_ages)
    state_ages = [
        state.operating_age_hours
        for state in dataset.machine_states
        if state.machine_id == machine_id and state.operating_age_hours is not None
    ]
    if state_ages:
        return max(state_ages)
    intervention_ages = [
        intervention.age_after_hours
        for intervention in dataset.maintenance_interventions
        if intervention.machine_id == machine_id
    ]
    return max(intervention_ages, default=0.0)


def _density_for(machine_id: str, config: MaintenanceAnalysisConfig) -> FailureDensityConfig:
    return config.machine_failure_densities.get(machine_id, config.default_failure_density)


def _urgency(
    failure_probability: float, anomaly_score: float, threshold: float
) -> Literal["low", "medium", "high", "critical"]:
    if failure_probability >= 0.75 or anomaly_score >= 2 * threshold:
        return "critical"
    if failure_probability >= 0.25 or anomaly_score >= threshold:
        return "high"
    if failure_probability >= 0.1 or anomaly_score >= 0.6 * threshold:
        return "medium"
    return "low"


def _action(policy: str, leading_variable: str | None, is_anomaly: bool) -> str:
    variable = leading_variable or "les conditions de fonctionnement"
    if policy == "corrective":
        if is_anomaly:
            return f"Préparer la réponse corrective et inspecter immédiatement {variable}."
        return f"Poursuivre sous surveillance et préparer la réponse corrective pour {variable}."
    if policy == "preventive":
        return f"Planifier une inspection et une maintenance préventive centrées sur {variable}."
    return f"Inspecter {variable}, confirmer l'anomalie, puis intervenir si elle est confirmée."


def analyze_dataset(
    dataset: MaintenanceDataset,
    config: MaintenanceAnalysisConfig,
) -> MaintenanceAnalysisResult:
    """Analyze all machines represented in a validated maintenance dataset."""

    by_machine: dict[str, list[SensorRecord]] = defaultdict(list)
    for record in dataset.sensor_records:
        if record.machine_id not in config.excluded_machine_ids:
            by_machine[record.machine_id].append(record)
    if not by_machine:
        raise ValueError("maintenance analysis requires at least one SensorRecord")

    assessments: list[MaintenanceAssessment] = []
    for machine_id in sorted(by_machine):
        records = by_machine[machine_id]
        anomaly = ewma_robust_anomaly(records, config)
        failures = [event for event in dataset.failure_events if event.machine_id == machine_id]
        interventions = [
            intervention
            for intervention in dataset.maintenance_interventions
            if intervention.machine_id == machine_id
        ]
        reliability = estimate_reliability(
            machine_id=machine_id,
            assessed_at=anomaly.assessed_at,
            operating_age_hours=_latest_operating_age(machine_id, dataset),
            horizon_hours=config.horizon_hours,
            density=_density_for(machine_id, config),
            confidence_level=config.confidence_level,
            evidence_points=len(records) + len(failures) + len(interventions),
        )
        comparison = compare_maintenance_policies(anomaly, reliability, config)
        economic_best = min(comparison, key=lambda item: (item.expected_cost, item.policy))
        risk_triggered = (
            anomaly.is_anomaly
            or reliability.failure_probability >= config.predictive_risk_threshold
        )
        selected = (
            next(item for item in comparison if item.policy == "predictive")
            if risk_triggered
            else economic_best
        )
        importance = anomaly.variable_importance
        leading_variable = (
            max(importance, key=lambda name: importance[name]) if importance else None
        )
        available_hours = max(
            0.25,
            min(config.horizon_hours, max(reliability.rul_lower_hours, 0.25)),
        )
        window_end = anomaly.assessed_at + timedelta(hours=available_hours)
        confidence = min(
            1.0,
            0.5 * reliability.confidence
            + 0.5 * min(1.0, anomaly.observations_used / config.minimum_baseline_points),
        )
        rationale = [
            f"Probabilité conditionnelle de panne Weibull : {reliability.failure_probability:.1%}.",
            f"Score EWMA robuste : {anomaly.score:.2f} (seuil {anomaly.threshold:.2f}).",
            f"Référence économique : {economic_best.policy} à {economic_best.expected_cost:.2f} {economic_best.currency}.",
        ]
        if selected.policy != economic_best.policy:
            rationale.append(
                "Politique prédictive retenue par le seuil de sécurité anomalie/risque."
            )
        if config.economics.assumptions_are_synthetic:
            rationale.append("Les coefficients économiques sont des hypothèses synthétiques.")
        recommendation = MaintenanceRecommendation(
            recommendation_id=(
                "maintenance-"
                + hashlib.sha256(
                    f"{machine_id}|{anomaly.assessed_at.isoformat()}".encode()
                ).hexdigest()[:12]
            ),
            machine_id=machine_id,
            created_at=anomaly.assessed_at,
            action=_action(selected.policy, leading_variable, anomaly.is_anomaly),
            urgency=_urgency(reliability.failure_probability, anomaly.score, anomaly.threshold),
            confidence=confidence,
            due_at=window_end,
            policy=selected.policy,
            intervention_window_start=anomaly.assessed_at,
            intervention_window_end=window_end,
            variable_importance=importance,
            expected_cost=selected.expected_cost,
            currency=selected.currency,
            rationale=rationale,
            provenance="module_b",
        )
        assessments.append(
            MaintenanceAssessment(
                assessment_id=f"assessment-{recommendation.recommendation_id.removeprefix('maintenance-')}",
                machine_id=machine_id,
                created_at=anomaly.assessed_at,
                anomaly=anomaly,
                reliability=reliability,
                recommendation=recommendation,
                policy_comparison=comparison,
                data_provenance=("module_a" if dataset.provenance == "module_a" else "external"),
                provenance="module_b",
            )
        )
    return MaintenanceAnalysisResult(
        assessments=assessments,
        sensor_records=dataset.sensor_records,
        config=config,
    )


def analyze_maintenance_bundle(
    input_dir: str | Path,
    config_path: str | Path | None = None,
) -> MaintenanceAnalysisResult:
    """Load Module A tabular outputs and run the complete Module B baseline."""

    return analyze_dataset(
        load_module_a_outputs(input_dir),
        load_maintenance_config(config_path),
    )
