"""Reproducible multi-replication campaigns and stable flat exchange tables."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from statistics import fmean, stdev
from typing import Any

import yaml

from .graph import mapping
from .kpi import KPI_NAMES, calculate_kpis
from .simulator import SimulationResult, simulate

EXCHANGE_SCHEMA_VERSION = "1.0.0"
PRODUCER_VERSION = "0.4.0"
DEFAULT_PLOT_KPIS = (
    "quantity_produced",
    "service_rate",
    "material_loss_rate",
    "total_cost",
)

KPI_UNITS: dict[str, str] = {
    "quantity_produced": "roll",
    "service_rate": "ratio",
    "average_cycle_time": "minute",
    "utilization_rate": "ratio",
    "defect_rate": "ratio",
    "material_loss_rate": "ratio",
    "final_material_loss_rate": "ratio",
    "recycling_attempts": "event",
    "recycled_quantity": "roll_equivalent",
    "recycling_recovery_rate": "ratio",
    "downtime": "minute",
    "total_cost": "synthetic_currency_unit",
    "energy_consumption": "kWh",
    "simplified_oee": "ratio",
    "average_delay": "minute",
}

RUN_COLUMNS = [
    "schema_version",
    "producer_version",
    "data_classification",
    "provenance",
    "campaign_id",
    "scenario_id",
    "factory_id",
    "replication",
    "seed",
    "simulated_start_at",
    "simulated_end_at",
    "makespan_minutes",
    "runtime_seconds",
    "job_count",
    "accepted_job_count",
    "failure_count",
    "maintenance_intervention_count",
    *KPI_NAMES,
]

PRODUCT_COLUMNS = [
    "schema_version",
    "producer_version",
    "data_classification",
    "provenance",
    "campaign_id",
    "scenario_id",
    "replication",
    "seed",
    "product_id",
    "released_rolls",
    "accepted_rolls",
    "rejected_rolls",
    "final_loss_rolls",
    "recycled_rolls",
    "recycle_pass_count",
    "on_time_rolls",
    "service_rate",
    "average_cycle_time_minutes",
    "average_delay_minutes",
    "throughput_rolls_per_hour",
]

MACHINE_COLUMNS = [
    "schema_version",
    "producer_version",
    "data_classification",
    "provenance",
    "campaign_id",
    "scenario_id",
    "replication",
    "seed",
    "machine_id",
    "process_node_id",
    "operating_hours",
    "utilization_rate",
    "energy_kwh",
    "estimated_emissions_kg_co2e",
    "failure_count",
    "downtime_minutes",
    "maintenance_count",
    "maintenance_minutes",
    "cost_synthetic_currency_unit",
]

STATISTIC_COLUMNS = [
    "schema_version",
    "producer_version",
    "data_classification",
    "provenance",
    "campaign_id",
    "scenario_id",
    "kpi_name",
    "unit",
    "n",
    "mean",
    "standard_deviation",
    "minimum",
    "p05",
    "p25",
    "median",
    "p75",
    "p95",
    "maximum",
    "ci95_lower",
    "ci95_upper",
    "ci95_method",
]


@dataclass(frozen=True)
class CampaignConfig:
    """Validated execution settings independent of the simulation contracts."""

    campaign_id: str
    simulation_config: Path
    replications: int
    seed_start: int
    seed_step: int = 1
    effective_scenario_id: str | None = None
    order_quantity_multiplier: int = 1
    horizon_extension_days: int = 0
    interarrival_time_minutes: float | None = None
    campaign_purpose: str = "statistical_baseline"
    representative_replication: int | None = 1
    representative_selection_reason: str = "configured_validation_sample"
    data_classification: str = "synthetic_hypothesis_not_calibrated"
    provenance: str = "sylvapapers_discrete_event_simulation"
    plot_kpis: tuple[str, ...] = DEFAULT_PLOT_KPIS
    source_path: Path | None = None

    @property
    def seeds(self) -> tuple[int, ...]:
        return tuple(self.seed_start + index * self.seed_step for index in range(self.replications))


@dataclass
class CampaignResult:
    """In-memory campaign result; rows are already shaped for external exchange."""

    config: CampaignConfig
    runs: list[dict[str, Any]]
    statistics: list[dict[str, Any]]
    product_statistics: list[dict[str, Any]] = field(default_factory=list)
    machine_statistics: list[dict[str, Any]] = field(default_factory=list)
    representative_result: SimulationResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def load_campaign_config(path: str | Path) -> CampaignConfig:
    """Load and validate a YAML/JSON campaign configuration."""

    source = Path(path).resolve()
    if source.suffix.lower() == ".json":
        raw = json.loads(source.read_text(encoding="utf-8"))
    elif source.suffix.lower() in {".yaml", ".yml"}:
        raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    else:
        raise ValueError("Campaign configuration must be YAML or JSON")
    if not isinstance(raw, dict):
        raise ValueError("Campaign configuration must be a mapping")

    campaign_id = str(raw.get("campaign_id", "")).strip()
    simulation_config_value = str(raw.get("simulation_config", "")).strip()
    replications = int(raw.get("replications", 0))
    seed_start = int(raw.get("seed_start", 0))
    seed_step = int(raw.get("seed_step", 1))
    order_quantity_multiplier = int(raw.get("order_quantity_multiplier", 1))
    horizon_extension_days = int(raw.get("horizon_extension_days", 0))
    interarrival_value = raw.get("interarrival_time_minutes")
    interarrival_time_minutes = (
        float(interarrival_value) if interarrival_value is not None else None
    )
    representative_value = raw.get("representative_replication", 1)
    representative_replication = (
        int(representative_value) if representative_value is not None else None
    )
    if not campaign_id:
        raise ValueError("campaign_id is required")
    if not simulation_config_value:
        raise ValueError("simulation_config is required")
    if not 2 <= replications <= 10_000:
        raise ValueError("replications must be between 2 and 10000")
    if seed_start < 0:
        raise ValueError("seed_start must be non-negative")
    if seed_step <= 0:
        raise ValueError("seed_step must be positive")
    if not 1 <= order_quantity_multiplier <= 10_000:
        raise ValueError("order_quantity_multiplier must be between 1 and 10000")
    if not 0 <= horizon_extension_days <= 3650:
        raise ValueError("horizon_extension_days must be between 0 and 3650")
    if interarrival_time_minutes is not None and interarrival_time_minutes <= 0:
        raise ValueError("interarrival_time_minutes must be positive when provided")
    if (
        representative_replication is not None
        and not 1 <= representative_replication <= replications
    ):
        raise ValueError("representative_replication must reference an existing replication")

    plot_value = raw.get("plot_kpis", DEFAULT_PLOT_KPIS)
    if not isinstance(plot_value, list | tuple) or not plot_value:
        raise ValueError("plot_kpis must be a non-empty list")
    plot_kpis = tuple(str(value) for value in plot_value)
    if unknown := set(plot_kpis) - set(KPI_NAMES):
        raise ValueError(f"Unknown plot KPIs: {sorted(unknown)}")

    simulation_config = (source.parent / simulation_config_value).resolve()
    if not simulation_config.is_file():
        raise ValueError(f"simulation_config does not exist: {simulation_config}")
    return CampaignConfig(
        campaign_id=campaign_id,
        simulation_config=simulation_config,
        replications=replications,
        seed_start=seed_start,
        seed_step=seed_step,
        effective_scenario_id=(
            str(raw["effective_scenario_id"]).strip() if raw.get("effective_scenario_id") else None
        ),
        order_quantity_multiplier=order_quantity_multiplier,
        horizon_extension_days=horizon_extension_days,
        interarrival_time_minutes=interarrival_time_minutes,
        campaign_purpose=str(raw.get("campaign_purpose", "statistical_baseline")),
        representative_replication=representative_replication,
        representative_selection_reason=str(
            raw.get("representative_selection_reason", "configured_validation_sample")
        ),
        data_classification=str(
            raw.get("data_classification", "synthetic_hypothesis_not_calibrated")
        ),
        provenance=str(raw.get("provenance", "sylvapapers_discrete_event_simulation")),
        plot_kpis=plot_kpis,
        source_path=source,
    )


def _quantile(values: list[float], probability: float) -> float:
    """Return a linearly interpolated empirical quantile (R-7 convention)."""

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _aggregate(
    rows: list[dict[str, Any]], config: CampaignConfig, scenario_id: str
) -> list[dict[str, Any]]:
    statistics: list[dict[str, Any]] = []
    for kpi_name in KPI_NAMES:
        values = [float(row[kpi_name]) for row in rows]
        count = len(values)
        mean = fmean(values)
        standard_deviation = stdev(values) if count > 1 else 0.0
        margin = 1.96 * standard_deviation / math.sqrt(count) if count else 0.0
        statistics.append(
            {
                "schema_version": EXCHANGE_SCHEMA_VERSION,
                "producer_version": PRODUCER_VERSION,
                "data_classification": config.data_classification,
                "provenance": config.provenance,
                "campaign_id": config.campaign_id,
                "scenario_id": scenario_id,
                "kpi_name": kpi_name,
                "unit": KPI_UNITS[kpi_name],
                "n": count,
                "mean": round(mean, 6),
                "standard_deviation": round(standard_deviation, 6),
                "minimum": round(min(values), 6),
                "p05": round(_quantile(values, 0.05), 6),
                "p25": round(_quantile(values, 0.25), 6),
                "median": round(_quantile(values, 0.50), 6),
                "p75": round(_quantile(values, 0.75), 6),
                "p95": round(_quantile(values, 0.95), 6),
                "maximum": round(max(values), 6),
                "ci95_lower": round(mean - margin, 6),
                "ci95_upper": round(mean + margin, 6),
                "ci95_method": "normal_approximation_1.96_standard_error",
            }
        )
    return statistics


def _digest(value: Any) -> str:
    serialized = json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _extend_datetime(value: Any, days: int) -> Any:
    if days == 0:
        return value
    from datetime import timedelta

    if isinstance(value, datetime):
        return value + timedelta(days=days)
    try:
        return datetime.fromisoformat(str(value)) + timedelta(days=days)
    except ValueError:
        return value


def materialize_scenario(scenario: Any, config: CampaignConfig) -> dict[str, Any]:
    """Materialize the effective long-run scenario used by every replication."""

    data = mapping(scenario)
    data["scenario_id"] = config.effective_scenario_id or str(data.get("scenario_id", "unknown"))
    data["end_at"] = _extend_datetime(data.get("end_at"), config.horizon_extension_days)
    if config.interarrival_time_minutes is not None:
        data["interarrival_time"] = config.interarrival_time_minutes
    orders: list[dict[str, Any]] = []
    for raw_order in data.get("orders", []):
        order = mapping(raw_order)
        order["quantity"] = int(order.get("quantity", 0)) * config.order_quantity_multiplier
        order["due_at"] = _extend_datetime(order.get("due_at"), config.horizon_extension_days)
        orders.append(order)
    data["orders"] = orders
    return data


def _product_rows(
    result: Any,
    config: CampaignConfig,
    replication: int,
    scenario_id: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for job in result.jobs:
        grouped.setdefault(str(job.get("product_id", "unknown")), []).append(job)
    rows: list[dict[str, Any]] = []
    for product_id, jobs in sorted(grouped.items()):
        released = len(jobs)
        accepted = sum(bool(job.get("accepted", True)) for job in jobs)
        recycle_counts = [
            int(
                job.get(
                    "recycle_loop_count",
                    job.get("recycle_count", job.get("rework_count", 0)),
                )
                or 0
            )
            for job in jobs
        ]
        recycled = sum(
            count > 0 or bool(job.get("recycled", job.get("reworked", False)))
            for job, count in zip(jobs, recycle_counts, strict=True)
        )
        final_loss = sum(
            bool(
                job.get(
                    "final_material_loss",
                    job.get("final_loss", not bool(job.get("accepted", True))),
                )
            )
            for job in jobs
        )
        on_time = sum(
            bool(job.get("on_time", False)) and bool(job.get("accepted", True)) for job in jobs
        )
        rows.append(
            {
                "schema_version": EXCHANGE_SCHEMA_VERSION,
                "producer_version": PRODUCER_VERSION,
                "data_classification": config.data_classification,
                "provenance": config.provenance,
                "campaign_id": config.campaign_id,
                "scenario_id": scenario_id,
                "replication": replication,
                "seed": result.seed,
                "product_id": product_id,
                "released_rolls": released,
                "accepted_rolls": accepted,
                "rejected_rolls": released - accepted,
                "final_loss_rolls": final_loss,
                "recycled_rolls": recycled,
                "recycle_pass_count": sum(recycle_counts),
                "on_time_rolls": on_time,
                "service_rate": round(on_time / released if released else 0.0, 6),
                "average_cycle_time_minutes": round(
                    fmean(float(job.get("cycle_time", 0)) for job in jobs), 6
                ),
                "average_delay_minutes": round(
                    fmean(float(job.get("delay", 0)) for job in jobs), 6
                ),
                "throughput_rolls_per_hour": round(
                    accepted / (float(result.makespan) / 60) if result.makespan else 0.0,
                    6,
                ),
            }
        )
    return rows


def _machine_rows(
    result: Any,
    config: CampaignConfig,
    replication: int,
    scenario_id: str,
) -> list[dict[str, Any]]:
    machines = result.final_state.get("machines", {})
    operation_events = [
        event for event in result.events if event.get("event_type") == "operation_end"
    ]
    rows: list[dict[str, Any]] = []
    for machine_id, state in sorted(machines.items()):
        events = [
            event
            for event in operation_events
            if str(event.get("machine_instance_id") or event.get("machine_id")) == machine_id
        ]
        failures = [
            event for event in result.failure_events if str(event.get("machine_id")) == machine_id
        ]
        maintenance = [
            event
            for event in result.maintenance_interventions
            if str(event.get("machine_id")) == machine_id
        ]
        operating_minutes = sum(float(event.get("duration", 0)) for event in events)
        rows.append(
            {
                "schema_version": EXCHANGE_SCHEMA_VERSION,
                "producer_version": PRODUCER_VERSION,
                "data_classification": config.data_classification,
                "provenance": config.provenance,
                "campaign_id": config.campaign_id,
                "scenario_id": scenario_id,
                "replication": replication,
                "seed": result.seed,
                "machine_id": machine_id,
                "process_node_id": str(state.get("process_node_id", "unknown")),
                "operating_hours": round(operating_minutes / 60, 6),
                "utilization_rate": round(
                    operating_minutes / float(result.makespan) if result.makespan else 0.0, 6
                ),
                "energy_kwh": round(sum(float(event.get("energy", 0)) for event in events), 6),
                "estimated_emissions_kg_co2e": round(
                    sum(float(event.get("estimated_emissions_kg_co2e", 0)) for event in events),
                    6,
                ),
                "failure_count": len(failures),
                "downtime_minutes": round(
                    sum(
                        float(event.get("downtime_minutes", event.get("duration", 0)))
                        for event in failures
                    ),
                    6,
                ),
                "maintenance_count": len(maintenance),
                "maintenance_minutes": round(
                    sum(float(event.get("duration_minutes", 0)) for event in maintenance), 6
                ),
                "cost_synthetic_currency_unit": round(
                    sum(float(event.get("cost", 0)) for event in events), 6
                ),
            }
        )
    return rows


def run_campaign(
    factory: Any,
    scenario: Any,
    config: CampaignConfig,
    product: Any | None = None,
) -> CampaignResult:
    """Run deterministic replications by replacing only the scenario seed."""

    if config.replications < 1:
        raise ValueError("replications must be positive")
    if config.representative_replication is not None and not (
        1 <= config.representative_replication <= config.replications
    ):
        raise ValueError("representative_replication must reference an existing replication")
    factory_data = mapping(factory)
    source_scenario_data = mapping(scenario)
    scenario_data = materialize_scenario(source_scenario_data, config)
    scenario_id = str(scenario_data.get("scenario_id", "unknown"))
    factory_id = str(factory_data.get("factory_id", "unknown"))
    rows: list[dict[str, Any]] = []
    product_statistics: list[dict[str, Any]] = []
    machine_statistics: list[dict[str, Any]] = []
    representative_result: SimulationResult | None = None
    simulation_metadata: dict[str, Any] = {}
    for replication, seed in enumerate(config.seeds, start=1):
        replicated_scenario = {**scenario_data, "random_seed": seed}
        result = simulate(factory_data, replicated_scenario, product)
        if replication == 1:
            simulation_metadata = result.metadata
        if replication == config.representative_replication:
            representative_result = result
        kpis = calculate_kpis(result)
        rows.append(
            {
                "schema_version": EXCHANGE_SCHEMA_VERSION,
                "producer_version": PRODUCER_VERSION,
                "data_classification": config.data_classification,
                "provenance": config.provenance,
                "campaign_id": config.campaign_id,
                "scenario_id": scenario_id,
                "factory_id": factory_id,
                "replication": replication,
                "seed": seed,
                "simulated_start_at": str(scenario_data.get("start_at", "")),
                "simulated_end_at": str(scenario_data.get("end_at", "")),
                "makespan_minutes": round(result.makespan, 6),
                "runtime_seconds": result.runtime_seconds,
                "job_count": len(result.jobs),
                "accepted_job_count": sum(bool(job.get("accepted", True)) for job in result.jobs),
                "failure_count": len(result.failure_events),
                "maintenance_intervention_count": len(result.maintenance_interventions),
                **kpis,
            }
        )
        product_statistics.extend(_product_rows(result, config, replication, scenario_id))
        machine_statistics.extend(_machine_rows(result, config, replication, scenario_id))

    statistics = _aggregate(rows, config, scenario_id)
    metadata = {
        "schema_version": EXCHANGE_SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "data_classification": config.data_classification,
        "provenance": config.provenance,
        "campaign_id": config.campaign_id,
        "scenario_id": scenario_id,
        "factory_id": factory_id,
        "replications": config.replications,
        "jobs_per_replication": sum(
            int(order.get("quantity", 0)) for order in scenario_data["orders"]
        ),
        "total_planned_jobs": config.replications
        * sum(int(order.get("quantity", 0)) for order in scenario_data["orders"]),
        "simulation_runtime_seconds_total": round(
            sum(float(row["runtime_seconds"]) for row in rows), 6
        ),
        "engine_code_version": simulation_metadata.get("code_version", "unknown"),
        "seeds": list(config.seeds),
        "scenario_transform": {
            "source_scenario_id": source_scenario_data.get("scenario_id"),
            "effective_scenario_id": scenario_id,
            "order_quantity_multiplier": config.order_quantity_multiplier,
            "horizon_extension_days": config.horizon_extension_days,
            "interarrival_time_minutes": scenario_data.get("interarrival_time"),
            "campaign_purpose": config.campaign_purpose,
        },
        "representative_replication": config.representative_replication,
        "representative_seed": (
            config.seeds[config.representative_replication - 1]
            if config.representative_replication is not None
            else None
        ),
        "representative_selection_reason": config.representative_selection_reason,
        "representative_module_a_bundle": (
            "representative_module_a" if config.representative_replication is not None else None
        ),
        "simulation_config": str(config.simulation_config),
        "campaign_config": str(config.source_path) if config.source_path else None,
        "input_digests_sha256": {
            "factory": _digest(factory_data),
            "source_scenario": _digest(source_scenario_data),
            "effective_scenario": _digest(scenario_data),
        },
        "methods": {
            "quantiles": "linear_interpolation_R7",
            "ci95": "normal_approximation_1.96_standard_error_across_replications",
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "limitations": [
            "All values are synthetic engineering hypotheses and are not plant-calibrated.",
            "Replications vary the pseudo-random seed but share one factory and scenario.",
            "The 95% confidence interval uses a normal approximation, not bootstrap inference.",
        ],
    }
    return CampaignResult(
        config=config,
        runs=rows,
        statistics=statistics,
        product_statistics=product_statistics,
        machine_statistics=machine_statistics,
        representative_result=representative_result,
        metadata=metadata,
    )


def _safe_cell(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return f"'{value}"
    return value


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows({key: _safe_cell(row.get(key)) for key in columns} for row in rows)


def _column_dictionary() -> dict[str, Any]:
    common = {
        "schema_version": ("string", "none", "Exchange contract version."),
        "producer_version": ("string", "none", "SylvaPapers producer package version."),
        "data_classification": ("string", "none", "Synthetic or real-data classification."),
        "provenance": ("string", "none", "Producing system or data source."),
        "campaign_id": ("string", "none", "Stable campaign identifier."),
        "scenario_id": ("string", "none", "Simulation scenario identifier."),
    }
    run_specific = {
        "factory_id": ("string", "none", "Factory configuration identifier."),
        "replication": ("integer", "count", "One-based replication number."),
        "seed": ("integer", "none", "Pseudo-random seed used by this replication."),
        "simulated_start_at": ("datetime", "ISO-8601", "Configured simulation start."),
        "simulated_end_at": ("datetime", "ISO-8601", "Configured simulation end."),
        "makespan_minutes": ("number", "minute", "Last job completion time."),
        "runtime_seconds": ("number", "second", "Wall-clock runtime of the replication."),
        "job_count": ("integer", "roll", "Released jobs."),
        "accepted_job_count": ("integer", "roll", "Accepted finished jobs."),
        "failure_count": ("integer", "event", "Simulated failure events."),
        "maintenance_intervention_count": (
            "integer",
            "intervention",
            "Simulated maintenance interventions.",
        ),
        **{name: ("number", KPI_UNITS[name], f"Run-level KPI: {name}.") for name in KPI_NAMES},
    }
    statistic_specific = {
        "kpi_name": ("string", "none", "KPI technical identifier."),
        "unit": ("string", "none", "Unit of the KPI values on this row."),
        "n": ("integer", "replication", "Number of replications."),
        "mean": ("number", "see unit", "Arithmetic mean."),
        "standard_deviation": ("number", "see unit", "Sample standard deviation."),
        "minimum": ("number", "see unit", "Observed minimum."),
        "p05": ("number", "see unit", "Fifth empirical percentile."),
        "p25": ("number", "see unit", "Twenty-fifth empirical percentile."),
        "median": ("number", "see unit", "Median."),
        "p75": ("number", "see unit", "Seventy-fifth empirical percentile."),
        "p95": ("number", "see unit", "Ninety-fifth empirical percentile."),
        "maximum": ("number", "see unit", "Observed maximum."),
        "ci95_lower": ("number", "see unit", "Lower 95% confidence bound for the mean."),
        "ci95_upper": ("number", "see unit", "Upper 95% confidence bound for the mean."),
        "ci95_method": ("string", "none", "Confidence interval calculation method."),
    }
    exchange_identity = {
        "replication": ("integer", "count", "One-based replication number."),
        "seed": ("integer", "none", "Pseudo-random seed used by this replication."),
    }
    product_specific = {
        **exchange_identity,
        "product_id": ("string", "none", "Product technical identifier."),
        "released_rolls": ("integer", "roll", "Released product jobs."),
        "accepted_rolls": ("integer", "roll", "Accepted final rolls."),
        "rejected_rolls": ("integer", "roll", "Jobs not accepted at final quality control."),
        "final_loss_rolls": ("integer", "roll", "Jobs recorded as irreversible final loss."),
        "recycled_rolls": ("integer", "roll", "Jobs entering at least one recycle pass."),
        "recycle_pass_count": ("integer", "pass", "Total recycle passes across product jobs."),
        "on_time_rolls": ("integer", "roll", "Accepted rolls completed by their due date."),
        "service_rate": ("number", "ratio", "On-time accepted rolls divided by releases."),
        "average_cycle_time_minutes": ("number", "minute", "Mean job cycle time."),
        "average_delay_minutes": ("number", "minute", "Mean positive due-date delay."),
        "throughput_rolls_per_hour": (
            "number",
            "roll/hour",
            "Accepted product rolls divided by run makespan.",
        ),
    }
    machine_specific = {
        **exchange_identity,
        "machine_id": ("string", "none", "Physical machine identifier."),
        "process_node_id": ("string", "none", "Logical process node identifier."),
        "operating_hours": ("number", "hour", "Sum of completed operation durations."),
        "utilization_rate": ("number", "ratio", "Operating minutes divided by run makespan."),
        "energy_kwh": ("number", "kWh", "Simulated operation energy."),
        "estimated_emissions_kg_co2e": (
            "number",
            "kgCO2e",
            "Synthetic estimate from configured electricity factors.",
        ),
        "failure_count": ("integer", "event", "Simulated failures."),
        "downtime_minutes": ("number", "minute", "Failure downtime."),
        "maintenance_count": ("integer", "intervention", "Maintenance interventions."),
        "maintenance_minutes": ("number", "minute", "Maintenance duration."),
        "cost_synthetic_currency_unit": (
            "number",
            "synthetic_currency_unit",
            "Simulated operation cost, not an accounting amount.",
        ),
    }

    def describe(
        columns: list[str], specific: dict[str, tuple[str, str, str]]
    ) -> list[dict[str, str]]:
        definitions = {**common, **specific}
        return [
            {
                "name": column,
                "data_type": definitions[column][0],
                "unit": definitions[column][1],
                "description": definitions[column][2],
            }
            for column in columns
        ]

    return {
        "schema_version": EXCHANGE_SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "compatibility": "flat_UTF-8_CSV_no_monorepo_dependency",
        "tables": {
            "campaign_runs.csv": describe(RUN_COLUMNS, run_specific),
            "kpi_statistics.csv": describe(STATISTIC_COLUMNS, statistic_specific),
            "module_d_product_statistics.csv": describe(PRODUCT_COLUMNS, product_specific),
            "module_e_machine_statistics.csv": describe(MACHINE_COLUMNS, machine_specific),
        },
    }


def generate_campaign_plot(result: CampaignResult, output_dir: str | Path) -> Path:
    """Render selected run distributions with the mean and 95% mean CI."""

    output = Path(output_dir)
    cache = output / ".matplotlib"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plot_kpis = result.config.plot_kpis
    columns = min(2, len(plot_kpis))
    rows = math.ceil(len(plot_kpis) / columns)
    figure, axes = plt.subplots(rows, columns, figsize=(6 * columns, 3.5 * rows), squeeze=False)
    statistics = {str(row["kpi_name"]): row for row in result.statistics}
    for index, kpi_name in enumerate(plot_kpis):
        axis = axes[index // columns][index % columns]
        values = [float(row[kpi_name]) for row in result.runs]
        axis.hist(values, bins="auto", color="#2f6f4e", alpha=0.8, edgecolor="white")
        aggregate = statistics[kpi_name]
        mean = float(aggregate["mean"])
        axis.axvline(mean, color="#7d2535", linewidth=2, label="Moyenne")
        axis.axvspan(
            float(aggregate["ci95_lower"]),
            float(aggregate["ci95_upper"]),
            color="#d9a441",
            alpha=0.25,
            label="IC95 moyenne",
        )
        axis.set_title(kpi_name)
        axis.set_xlabel(KPI_UNITS[kpi_name])
        axis.set_ylabel("Réplications")
        axis.grid(alpha=0.2)
        axis.legend(fontsize=8)
    for index in range(len(plot_kpis), rows * columns):
        axes[index // columns][index % columns].axis("off")
    figure.suptitle("SylvaPapers — distributions synthétiques multi-réplications")
    figure.tight_layout()
    path = output / "kpi_distributions.png"
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def save_campaign(
    result: CampaignResult,
    output_dir: str | Path,
    *,
    plot: bool = True,
) -> dict[str, Path]:
    """Persist portable CSV/JSON contracts and the optional statistical figure."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "runs": output / "campaign_runs.csv",
        "statistics": output / "kpi_statistics.csv",
        "module_d_products": output / "module_d_product_statistics.csv",
        "module_e_machines": output / "module_e_machine_statistics.csv",
        "results": output / "campaign_results.json",
        "metadata": output / "campaign_metadata.json",
        "column_dictionary": output / "column_dictionary.json",
    }
    _write_csv(paths["runs"], result.runs, RUN_COLUMNS)
    _write_csv(paths["statistics"], result.statistics, STATISTIC_COLUMNS)
    _write_csv(paths["module_d_products"], result.product_statistics, PRODUCT_COLUMNS)
    _write_csv(paths["module_e_machines"], result.machine_statistics, MACHINE_COLUMNS)
    paths["results"].write_text(
        json.dumps(
            {
                "schema_version": EXCHANGE_SCHEMA_VERSION,
                "producer_version": PRODUCER_VERSION,
                "metadata": result.metadata,
                "runs": result.runs,
                "statistics": result.statistics,
                "module_d_product_statistics": result.product_statistics,
                "module_e_machine_statistics": result.machine_statistics,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    paths["metadata"].write_text(
        json.dumps(result.metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    paths["column_dictionary"].write_text(
        json.dumps(_column_dictionary(), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if result.representative_result is not None:
        from .reporting import save_result

        representative_output = output / "representative_module_a"
        save_result(result.representative_result, representative_output, plots=False)
        paths["representative_module_a"] = representative_output
    if plot:
        paths["plot"] = generate_campaign_plot(result, output)
    return paths
