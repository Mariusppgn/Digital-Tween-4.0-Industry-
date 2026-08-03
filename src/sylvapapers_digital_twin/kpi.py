"""Operational KPIs for production, reliability, quality, loss, energy and cost."""

from __future__ import annotations

from statistics import fmean

from .simulator import SimulationResult

KPI_NAMES = (
    "quantity_produced",
    "service_rate",
    "average_cycle_time",
    "utilization_rate",
    "defect_rate",
    "material_loss_rate",
    "final_material_loss_rate",
    "recycling_attempts",
    "recycled_quantity",
    "recycling_recovery_rate",
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
    accepted_jobs = [job for job in jobs if bool(job.get("accepted", True))]
    quantity, makespan = len(accepted_jobs), result.makespan
    released_quantity = len(jobs)
    capacity = sum(result.machine_capacities.values())
    available_minutes = makespan * capacity
    productive = sum(float(event.get("duration", 0)) for event in operations)
    downtime = sum(float(event.get("duration", 0)) for event in failures)
    utilization = productive / available_minutes if available_minutes else 0.0
    defect_rate = len(defects) / len(checks) if checks else 0.0
    recycling_attempts = sum(
        bool(record.get("recovery_attempted", False)) for record in result.recycling_records
    )
    recycled_quantity = sum(
        float(record.get("recovered_quantity", 0)) for record in result.recycling_records
    )
    final_material_loss = sum(float(job.get("final_material_loss", 0)) for job in jobs)
    availability = max(0.0, 1 - downtime / available_minutes) if available_minutes else 0.0
    # Performance is deliberately simple for this first executable baseline.
    performance = min(1.0, utilization)
    values = {
        "quantity_produced": quantity,
        "service_rate": (
            sum(bool(job["on_time"]) and bool(job.get("accepted", True)) for job in jobs)
            / released_quantity
            if released_quantity
            else 0.0
        ),
        "average_cycle_time": fmean(float(job["cycle_time"]) for job in jobs) if jobs else 0.0,
        "utilization_rate": utilization,
        "defect_rate": defect_rate,
        "material_loss_rate": (
            sum(float(job.get("material_loss", 0)) for job in jobs) / released_quantity
            if released_quantity
            else 0.0
        ),
        "final_material_loss_rate": (
            final_material_loss / released_quantity if released_quantity else 0.0
        ),
        "recycling_attempts": recycling_attempts,
        "recycled_quantity": recycled_quantity,
        "recycling_recovery_rate": (
            recycled_quantity / recycling_attempts if recycling_attempts else 0.0
        ),
        "downtime": downtime,
        "total_cost": sum(float(event.get("cost", 0)) for event in result.events),
        "energy_consumption": sum(float(event.get("energy", 0)) for event in operations),
        "simplified_oee": availability * performance * (1 - defect_rate),
        "average_delay": fmean(float(job["delay"]) for job in jobs) if jobs else 0.0,
    }
    return {name: round(float(values[name]), 6) for name in KPI_NAMES}
