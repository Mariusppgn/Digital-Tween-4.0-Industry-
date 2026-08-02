"""Deterministic machine-readable and visual Module B outputs."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sylvapapers_contracts import SensorRecord

from .service import MaintenanceAnalysisResult


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


def save_maintenance_analysis(
    result: MaintenanceAnalysisResult,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Persist contracts, economic comparison and three reproducible figures."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    assessments_path = destination / "maintenance_assessments.json"
    costs_path = destination / "maintenance_policy_costs.csv"
    sensor_figure = destination / "sensor_anomalies.png"
    reliability_figure = destination / "failure_risk_rul.png"
    policy_figure = destination / "maintenance_policy_costs.png"

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
                        "machine_id": _csv_safe(assessment.machine_id),
                        "policy": policy.policy,
                        "expected_cost": round(policy.expected_cost, 6),
                        "currency": policy.currency,
                        "expected_downtime_hours": round(policy.expected_downtime_hours, 6),
                        "intervention_probability": round(policy.intervention_probability, 9),
                        "assumptions_are_synthetic": policy.assumptions_are_synthetic,
                    }
                )
    _plot_sensor_anomalies(result, sensor_figure)
    _plot_risk_rul(result, reliability_figure)
    _plot_policy_costs(result, policy_figure)
    return {
        "assessments": assessments_path,
        "policy_costs": costs_path,
        "sensor_anomalies_figure": sensor_figure,
        "failure_risk_rul_figure": reliability_figure,
        "policy_costs_figure": policy_figure,
    }
