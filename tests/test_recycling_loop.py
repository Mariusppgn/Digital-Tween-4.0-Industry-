from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from sylvapapers_contracts import FactoryConfig
from sylvapapers_digital_twin import build_process_graph, save_result, simulate
from sylvapapers_digital_twin.kpi import calculate_kpis


def _factory(*, enabled: bool, recovery_yield: float = 1.0, max_loops: int = 2):
    return {
        "factory_id": "recycling-test",
        "name": "Recycling test mill",
        "machines": [
            {
                "machine_id": "repulper-01",
                "name": "Repulper",
                "machine_type": "process",
                "capabilities": ["repulping"],
                "capacity_per_hour": 60,
                "metadata": {"processing_time": 1, "energy_kw": 10},
            },
            {
                "machine_id": "qc-01",
                "name": "Quality control",
                "machine_type": "quality_control",
                "capabilities": ["quality_control"],
                "capacity_per_hour": 60,
                "metadata": {"processing_time": 1, "defect_rate": 1},
            },
        ],
        "process_graph": {
            "recycling": {
                "enabled": enabled,
                "source_node_id": "quality-control",
                "return_to_node_id": "repulping",
                "recovery_yield": recovery_yield,
                "max_loops": max_loops,
                "quantity_unit": "roll_equivalent",
            },
            "nodes": [
                {"node_id": "raw", "kind": "source", "name": "Raw"},
                {
                    "node_id": "repulping",
                    "kind": "operation",
                    "name": "Repulping",
                    "machine_ids": ["repulper-01"],
                },
                {
                    "node_id": "quality-control",
                    "kind": "quality_control",
                    "name": "Quality control",
                    "machine_ids": ["qc-01"],
                },
                {"node_id": "finished", "kind": "sink", "name": "Finished"},
                {"node_id": "loss", "kind": "sink", "name": "Loss"},
            ],
            "edges": [
                {"source": "raw", "target": "repulping"},
                {"source": "repulping", "target": "quality-control"},
                {"source": "quality-control", "target": "finished"},
                {"source": "quality-control", "target": "loss"},
                {
                    "source": "quality-control",
                    "target": "repulping",
                    "relation": "recycle",
                },
            ],
        },
    }


def _scenario(quantity: int = 2):
    return {
        "scenario_id": "recycling-loop",
        "random_seed": 1234,
        "products": [
            {
                "product_id": "paper-roll",
                "name": "Paper roll",
                "routing": ["repulping", "quality-control"],
            }
        ],
        "orders": [
            {
                "order_id": "ORDER",
                "product_id": "paper-roll",
                "quantity": quantity,
                "due_at": 1_000,
            }
        ],
    }


def test_enabled_recycling_is_reproducible_bounded_and_conservative() -> None:
    first = simulate(_factory(enabled=True), _scenario())
    second = simulate(_factory(enabled=True), _scenario())

    assert first.events == second.events
    assert first.jobs == second.jobs
    assert first.recycling_records == second.recycling_records
    assert len(first.jobs) == 2
    assert all(job["recycle_loop_count"] == 2 for job in first.jobs)
    assert all(job["quality_rejections"] == 3 for job in first.jobs)
    assert all(job["final_material_loss"] == 1 for job in first.jobs)
    assert sum(row["outcome"] == "recycled" for row in first.recycling_records) == 4
    assert sum(row["outcome"] == "max_loops_reached" for row in first.recycling_records) == 2
    assert sum(event["event_type"] == "recycling_return" for event in first.events) == 4
    assert first.final_state["totals"]["recycled_quantity"] == 4
    assert first.final_state["totals"]["final_material_loss_quantity"] == 2
    assert first.final_state["totals"]["material_balance_error"] == 0
    assert first.final_state["work_in_progress"] == 0

    kpis = calculate_kpis(first)
    assert kpis["recycling_attempts"] == 4
    assert kpis["recycled_quantity"] == 4
    assert kpis["recycling_recovery_rate"] == 1
    assert kpis["final_material_loss_rate"] == 1


def test_disabled_recycling_records_final_loss_without_feedback() -> None:
    result = simulate(_factory(enabled=False), _scenario(quantity=1))

    assert result.jobs[0]["recycle_loop_count"] == 0
    assert result.jobs[0]["final_material_loss"] == 1
    assert [row["outcome"] for row in result.recycling_records] == ["disabled_final_loss"]
    assert not any(event["event_type"] == "recycling_return" for event in result.events)
    assert result.final_state["totals"]["recycled_quantity"] == 0
    assert result.final_state["totals"]["material_balance_error"] == 0


def test_recycling_exchange_csv_distinguishes_recovered_and_final_loss(tmp_path: Path) -> None:
    result = simulate(_factory(enabled=True), _scenario(quantity=1))
    save_result(result, tmp_path, plots=False)

    with (tmp_path / "recycling.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert [row["outcome"] for row in rows] == [
        "recycled",
        "recycled",
        "max_loops_reached",
    ]
    assert sum(float(row["recovered_quantity"]) for row in rows) == 2
    assert sum(float(row["unrecoverable_quantity"]) for row in rows) == 1
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["recycling_record_count"] == 3
    assert "recycling.csv" in summary["detailed_outputs"]


def test_graph_accepts_only_one_explicit_feedback_around_an_acyclic_flow() -> None:
    factory = _factory(enabled=True)
    validated = FactoryConfig.model_validate(factory)
    graph = build_process_graph(validated)
    assert graph.edges["quality-control", "repulping"]["relation"] == "recycle"
    assert graph.graph["recycling"]["max_loops"] == 2

    unsafe = deepcopy(factory)
    unsafe["process_graph"]["edges"].append(  # type: ignore[index,union-attr]
        {"source": "quality-control", "target": "raw"}
    )
    with pytest.raises(ValidationError, match="acyclic"):
        FactoryConfig.model_validate(unsafe)

    missing_controls = deepcopy(factory)
    del missing_controls["process_graph"]["recycling"]  # type: ignore[index,union-attr]
    with pytest.raises(ValidationError, match="explicit recycling configuration"):
        FactoryConfig.model_validate(missing_controls)
