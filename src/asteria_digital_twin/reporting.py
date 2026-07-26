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


def _csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write heterogeneous event dictionaries as a rectangular UTF-8 CSV file."""
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


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
        "machines": list(result.graph.nodes),
        "metadata": result.metadata,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "output_directory": str(output.resolve()),
        "kpis": kpis,
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
        "# Asteria simulation report",
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
        "- The model represents operational flow, not detailed composite physics.",
        "- Human calendars and material inventories are simplified in this first delivery.",
        "",
    ]
    path = destination / "simulation_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
