"""Transparent economic comparison of maintenance policies."""

from __future__ import annotations

from sylvapapers_contracts import (
    AnomalyResult,
    MaintenanceAnalysisConfig,
    MaintenancePolicyCost,
    ReliabilityEstimate,
)


def compare_maintenance_policies(
    anomaly: AnomalyResult,
    reliability: ReliabilityEstimate,
    config: MaintenanceAnalysisConfig,
) -> list[MaintenancePolicyCost]:
    """Compare corrective, preventive and predictive expected costs.

    The formulas deliberately remain simple and auditable. Default monetary
    assumptions are synthetic and are labelled as such in every output row.
    """

    costs = config.economics
    failure_consequence = (
        costs.corrective_intervention_cost
        + costs.corrective_downtime_hours * costs.downtime_cost_per_hour
    ) * config.criticality
    planned_consequence = costs.planned_downtime_hours * costs.downtime_cost_per_hour
    failure_probability = reliability.failure_probability
    anomaly_trigger = min(1.0, anomaly.score / anomaly.threshold)

    corrective_cost = failure_probability * failure_consequence
    preventive_residual = failure_probability * (1 - costs.preventive_age_recovery)
    preventive_cost = (
        costs.preventive_intervention_cost
        + planned_consequence
        + preventive_residual * failure_consequence
    )
    predictive_probability = max(failure_probability, anomaly_trigger)
    predictive_residual = failure_probability * (
        1 - predictive_probability * costs.predictive_effectiveness
    )
    predictive_cost = (
        predictive_probability * (costs.predictive_intervention_cost + planned_consequence)
        + predictive_residual * failure_consequence
    )

    return [
        MaintenancePolicyCost(
            policy="corrective",
            expected_cost=corrective_cost,
            currency=costs.currency,
            expected_downtime_hours=(failure_probability * costs.corrective_downtime_hours),
            intervention_probability=failure_probability,
            assumptions_are_synthetic=costs.assumptions_are_synthetic,
            rationale=["Coût engagé uniquement en cas de panne dans l'horizon prédit."],
            provenance="module_b",
        ),
        MaintenancePolicyCost(
            policy="preventive",
            expected_cost=preventive_cost,
            currency=costs.currency,
            expected_downtime_hours=(
                costs.planned_downtime_hours + preventive_residual * costs.corrective_downtime_hours
            ),
            intervention_probability=1,
            assumptions_are_synthetic=costs.assumptions_are_synthetic,
            rationale=["Une intervention planifiée, plus le risque Weibull résiduel."],
            provenance="module_b",
        ),
        MaintenancePolicyCost(
            policy="predictive",
            expected_cost=predictive_cost,
            currency=costs.currency,
            expected_downtime_hours=(
                predictive_probability * costs.planned_downtime_hours
                + predictive_residual * costs.corrective_downtime_hours
            ),
            intervention_probability=predictive_probability,
            assumptions_are_synthetic=costs.assumptions_are_synthetic,
            rationale=[
                "La probabilité d'intervention combine le risque Weibull et l'anomalie EWMA."
            ],
            provenance="module_b",
        ),
    ]
