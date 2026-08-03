"""End-to-end acceptance checks for the reference fast scenario."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import networkx as nx

from sylvapapers_contracts import load_factory_config, load_simulation_scenario
from sylvapapers_digital_twin import KPI_NAMES, calculate_kpis, save_result, simulate

ROOT = Path(__file__).resolve().parents[1]


def _maximum_concurrency(result_events: list[dict[str, object]]) -> dict[str, int]:
    timeline: dict[str, list[tuple[float, int]]] = defaultdict(list)
    for event in result_events:
        if event["event_type"] != "operation_end":
            continue
        machine = str(event["machine_id"])
        end = float(event["time"])
        start = float(event["started_at"])
        timeline[machine].extend([(start, 1), (end, -1)])
    maxima: dict[str, int] = {}
    for machine, points in timeline.items():
        active = 0
        maximum = 0
        for _, delta in sorted(points, key=lambda item: (item[0], item[1])):
            active += delta
            maximum = max(maximum, active)
        maxima[machine] = maximum
    return maxima


def test_fast_baseline_is_deterministic_and_respects_core_invariants() -> None:
    factory = load_factory_config(ROOT / "configs" / "factory.yaml")
    scenario = load_simulation_scenario(ROOT / "data" / "examples" / "simulation_scenario.json")
    first = simulate(factory, scenario)
    second = simulate(factory, scenario)

    assert first.events == second.events
    assert first.jobs == second.jobs
    assert len(first.jobs) == 10
    assert first.runtime_seconds < 30
    nominal_graph = nx.DiGraph(
        (source, target)
        for source, target, attributes in first.graph.edges(data=True)
        if attributes.get("relation", "forward") == "forward"
    )
    assert nx.is_directed_acyclic_graph(nominal_graph)
    assert any(
        attributes.get("relation") == "recycle" for _, _, attributes in first.graph.edges(data=True)
    )
    assert first.machine_capacities["drying"] == 2
    assert all(float(event.get("inventory", 0)) >= 0 for event in first.events)

    concurrency = _maximum_concurrency(first.events)
    assert all(
        concurrency.get(machine, 0) <= capacity
        for machine, capacity in first.machine_capacities.items()
    )

    event_types = {str(event["event_type"]) for event in first.events}
    assert {"setup", "operation_start", "operation_end", "qc_pass", "completed"} <= event_types
    assert "rework" not in event_types


def test_fast_baseline_exports_kpis_and_three_figures(tmp_path: Path) -> None:
    factory = load_factory_config(ROOT / "configs" / "factory.yaml")
    scenario = load_simulation_scenario(ROOT / "data" / "examples" / "simulation_scenario.json")
    result = simulate(factory, scenario)
    kpis = calculate_kpis(result)
    paths = save_result(result, tmp_path)

    assert len(kpis) == len(KPI_NAMES) == 21
    assert kpis["quantity_produced"] == 10
    assert kpis["energy_consumption"] > 0
    assert kpis["total_cost"] > 0
    assert {name for name in paths if name.endswith("_plot")} == {
        "throughput_plot",
        "utilization_plot",
        "kpi_plot",
        "revenue_plot",
    }
    assert all(path.stat().st_size > 100 for path in paths.values())
