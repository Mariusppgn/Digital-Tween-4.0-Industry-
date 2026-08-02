"""Persistence, figures and a lightweight Markdown experiment report."""

from __future__ import annotations

import csv
import json
import os
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .kpi import calculate_kpis
from .simulator import SimulationResult


def _csv(
    path: Path,
    rows: list[dict[str, Any]],
    fields: list[str] | None = None,
) -> None:
    """Write heterogeneous event dictionaries as a rectangular UTF-8 CSV file."""
    fieldnames = fields or sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(
            {
                key: (
                    f"'{value}"
                    if isinstance(value, str) and value.startswith(("=", "+", "-", "@"))
                    else value
                )
                for key, value in row.items()
            }
            for row in rows
        )


def save_result(
    result: SimulationResult,
    output_dir: str | Path,
    plots: bool = True,
) -> dict[str, Path]:
    """Persist an experiment bundle and optionally render three PNG figures."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    kpis = calculate_kpis(result)
    paths = {
        "events": output / "events.csv",
        "jobs": output / "jobs.csv",
        "kpis": output / "kpis.json",
        "summary": output / "summary.json",
    }
    _csv(paths["events"], result.events)
    _csv(paths["jobs"], result.jobs)
    # Stable A-to-B exchange tables are always persisted. They intentionally
    # remain outside ``paths`` to preserve the original public return contract.
    detailed_tables: dict[str, tuple[list[dict[str, Any]], list[str]]] = {
        "machine_states.csv": (
            result.machine_states,
            [
                "machine_id",
                "process_node_id",
                "instance_index",
                "time_minutes",
                "timestamp",
                "status",
                "job_id",
                "operating_age_hours",
                "remaining_minutes",
                "utilisation",
            ],
        ),
        "sensors.csv": (
            result.sensor_records,
            [
                "sensor_id",
                "machine_id",
                "process_node_id",
                "time_minutes",
                "timestamp",
                "job_id",
                "quality",
                "load_ratio",
                "temperature_c",
                "vibration_mm_s",
                "pressure_bar",
                "power_kw",
                "operating_age_hours",
                "degradation_index",
                "failure_probability",
                "synthetic",
            ],
        ),
        "failures.csv": (
            result.failure_events,
            [
                "failure_id",
                "machine_id",
                "process_node_id",
                "time_minutes",
                "timestamp",
                "job_id",
                "failure_mode",
                "severity",
                "downtime_minutes",
                "failure_probability",
                "operating_age_hours",
                "synthetic",
            ],
        ),
        "maintenance.csv": (
            result.maintenance_interventions,
            [
                "intervention_id",
                "machine_id",
                "process_node_id",
                "time_minutes",
                "timestamp",
                "completed_at_minutes",
                "completed_at",
                "job_id",
                "maintenance_type",
                "duration_minutes",
                "age_before_hours",
                "age_after_hours",
                "recovery_fraction",
                "technician_resource",
                "synthetic",
            ],
        ),
        "queues.csv": (
            result.queue_history,
            [
                "machine_id",
                "time_minutes",
                "timestamp",
                "job_id",
                "arrival_minutes",
                "service_start_minutes",
                "wait_minutes",
                "queue_length",
                "buffer_capacity",
                "buffer_index",
            ],
        ),
        "work_in_progress.csv": (
            result.work_in_progress,
            [
                "time_minutes",
                "timestamp",
                "job_id",
                "product_id",
                "process_node_id",
                "status",
                "wip_delta",
                "total_wip",
            ],
        ),
    }
    for filename, (rows, fields) in detailed_tables.items():
        _csv(output / filename, rows, fields)
    (output / "final_state.json").write_text(
        json.dumps(result.final_state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    paths["kpis"].write_text(
        json.dumps(kpis, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "seed": result.seed,
        "makespan_minutes": result.makespan,
        "runtime_seconds": result.runtime_seconds,
        "event_count": len(result.events),
        "job_count": len(result.jobs),
        "machine_state_count": len(result.machine_states),
        "sensor_record_count": len(result.sensor_records),
        "failure_count": len(result.failure_events),
        "maintenance_intervention_count": len(result.maintenance_interventions),
        "queue_record_count": len(result.queue_history),
        "wip_record_count": len(result.work_in_progress),
        "machines": list(result.graph.nodes),
        "metadata": result.metadata,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "output_directory": str(output.resolve()),
        "kpis": kpis,
        "detailed_outputs": [*detailed_tables, "final_state.json"],
    }
    paths["summary"].write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    if plots:
        paths.update(generate_plots(result, output))
    return paths


def generate_plots(
    result: SimulationResult,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Render cumulative production, utilization and KPI charts headlessly."""
    output = Path(output_dir)
    cache = output / ".matplotlib"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache))

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    paths: dict[str, Path] = {}

    figure, axes = plt.subplots(figsize=(7, 4))
    axes.step(
        [job["completion_time"] for job in result.jobs],
        range(1, len(result.jobs) + 1),
        where="post",
    )
    axes.set(
        title="Production cumulée",
        xlabel="Temps simulé (min)",
        ylabel="Pièces terminées",
    )
    axes.grid(alpha=0.25)
    paths["throughput_plot"] = output / "throughput.png"
    figure.tight_layout()
    figure.savefig(paths["throughput_plot"], dpi=140)
    plt.close(figure)

    busy = {machine: 0.0 for machine in result.graph.nodes}
    for event in result.events:
        if event["event_type"] == "operation_end":
            busy[event["machine_id"]] += float(event["duration"])
    figure, axes = plt.subplots(figsize=(8, 4))
    labels = list(busy)
    values = [
        busy[label] / max(result.makespan * result.machine_capacities.get(label, 1), 1)
        for label in labels
    ]
    axes.bar(labels, values)
    axes.set(title="Utilisation par poste", ylabel="Taux", ylim=(0, 1))
    axes.tick_params(axis="x", rotation=25)
    paths["utilization_plot"] = output / "utilization.png"
    figure.tight_layout()
    figure.savefig(paths["utilization_plot"], dpi=140)
    plt.close(figure)

    kpis = calculate_kpis(result)
    figure, axes = plt.subplots(figsize=(7, 4))
    axes.bar(
        ["Service", "Utilisation", "Qualité", "OEE"],
        [
            kpis["service_rate"],
            kpis["utilization_rate"],
            1 - kpis["defect_rate"],
            kpis["simplified_oee"],
        ],
    )
    axes.set(title="Indicateurs synthétiques", ylabel="Taux", ylim=(0, 1))
    paths["kpi_plot"] = output / "kpis.png"
    figure.tight_layout()
    figure.savefig(paths["kpi_plot"], dpi=140)
    plt.close(figure)

    operations = [event for event in result.events if event["event_type"] == "operation_end"]
    figure, axes = plt.subplots(figsize=(10, max(4, len(result.graph.nodes) * 0.3)))
    machine_order = {machine: index for index, machine in enumerate(result.graph.nodes)}
    for event in operations:
        machine = str(event["machine_id"])
        axes.barh(
            machine_order[machine],
            float(event["duration"]),
            left=float(event["started_at"]),
            height=0.65,
            alpha=0.8,
        )
    axes.set_yticks(list(machine_order.values()), labels=list(machine_order))
    axes.set(title="Gantt des machines", xlabel="Temps simulé (min)")
    axes.grid(axis="x", alpha=0.25)
    paths["machine_gantt"] = output / "machine_gantt.png"
    figure.tight_layout()
    figure.savefig(paths["machine_gantt"], dpi=140)
    plt.close(figure)

    figure, axes = plt.subplots(figsize=(8, 4))
    by_machine: dict[str, list[dict[str, Any]]] = {}
    for row in result.queue_history:
        by_machine.setdefault(str(row["machine_id"]), []).append(row)
    for machine, rows in by_machine.items():
        if any(float(row["wait_minutes"]) > 0 for row in rows):
            axes.step(
                [float(row["time_minutes"]) for row in rows],
                [int(row["queue_length"]) for row in rows],
                where="post",
                label=machine,
            )
    axes.set(title="Évolution des files d’attente", xlabel="Temps simulé (min)", ylabel="Jobs")
    if axes.lines:
        axes.legend(fontsize=7, ncol=2)
    axes.grid(alpha=0.25)
    paths["queue_history"] = output / "queue_history.png"
    figure.tight_layout()
    figure.savefig(paths["queue_history"], dpi=140)
    plt.close(figure)

    energy_by_machine: dict[str, float] = {}
    for event in operations:
        machine = str(event["machine_id"])
        energy_by_machine[machine] = energy_by_machine.get(machine, 0.0) + float(
            event.get("energy", 0)
        )
    figure, axes = plt.subplots(figsize=(9, 4))
    axes.bar(list(energy_by_machine), list(energy_by_machine.values()))
    axes.set(title="Énergie par étape", ylabel="kWh")
    axes.tick_params(axis="x", rotation=30)
    paths["energy_by_machine"] = output / "energy_by_machine.png"
    figure.tight_layout()
    figure.savefig(paths["energy_by_machine"], dpi=140)
    plt.close(figure)
    return paths


def generate_markdown_report(
    input_dir: str | Path,
    output_dir: str | Path,
) -> Path:
    """Generate a readable Markdown report from a saved experiment bundle."""
    source = Path(input_dir)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    summary = json.loads((source / "summary.json").read_text(encoding="utf-8"))
    kpis = json.loads((source / "kpis.json").read_text(encoding="utf-8"))
    lines = [
        "# SylvaPapers paper-mill simulation report",
        "",
        "## Reproducibility",
        "",
        f"- Scenario: `{summary['metadata']['scenario_id']}`",
        f"- Factory: `{summary['metadata']['factory_id']}`",
        f"- Random seed: `{summary['seed']}`",
        f"- Schema version: `{summary['metadata']['schema_version']}`",
        f"- Code version: `{summary['metadata']['code_version']}`",
        f"- Runtime: `{summary['runtime_seconds']} s`",
        "",
        "## KPI",
        "",
        "| Metric | Value |",
        "|---|---:|",
        *[f"| `{name}` | {value} |" for name, value in kpis.items()],
        "",
        "## Assumptions and limits",
        "",
        "- All baseline values and events are synthetic.",
        "- The model represents operational paper-mill flow, not detailed fibre or fluid physics.",
        "- Quality rejects are measured as material losses; no recycling loop is simulated.",
        "- Human calendars and material inventories are simplified in this first delivery.",
        "",
    ]
    path = destination / "simulation_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
