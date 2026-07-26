"""The ten initial operational KPIs."""

from __future__ import annotations

from statistics import fmean

from .simulator import SimulationResult

KPI_NAMES = (
    "quantity_produced",
    "service_rate",
    "average_cycle_time",
    "utilization_rate",
    "defect_rate",
    "downtime",
    "total_cost",
    "energy_consumption",
    "simplified_oee",
    "average_delay",
)


def calculate_kpis(result: SimulationResult) -> dict[str, float]:
    jobs = result.jobs
    operations = [event for event in result.events if event["event_type"] == "operation_end"]
    failures = [event for event in result.events if event["event_type"] == "breakdown"]
    checks = [event for event in result.events if event["event_type"] in {"qc_pass", "qc_fail"}]
    defects = [event for event in checks if event["event_type"] == "qc_fail"]
    quantity, makespan = len(jobs), result.makespan
    capacity = sum(result.machine_capacities.values())
    available_minutes = makespan * capacity
    productive = sum(float(event.get("duration", 0)) for event in operations)
    downtime = sum(float(event.get("duration", 0)) for event in failures)
    utilization = productive / available_minutes if available_minutes else 0.0
    defect_rate = len(defects) / len(checks) if checks else 0.0
    availability = max(0.0, 1 - downtime / available_minutes) if available_minutes else 0.0
    # Performance is deliberately simple for this first executable baseline.
    performance = min(1.0, utilization)
    values = {
        "quantity_produced": quantity,
        "service_rate": sum(bool(job["on_time"]) for job in jobs) / quantity if quantity else 0.0,
        "average_cycle_time": fmean(float(job["cycle_time"]) for job in jobs) if jobs else 0.0,
        "utilization_rate": utilization,
        "defect_rate": defect_rate,
        "downtime": downtime,
        "total_cost": sum(float(event.get("cost", 0)) for event in result.events),
        "energy_consumption": sum(float(event.get("energy", 0)) for event in operations),
        "simplified_oee": availability * performance * (1 - defect_rate),
        "average_delay": fmean(float(job["delay"]) for job in jobs) if jobs else 0.0,
    }
    return {name: round(float(values[name]), 6) for name in KPI_NAMES}
