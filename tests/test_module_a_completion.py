from __future__ import annotations

import csv
import json
from pathlib import Path

from sylvapapers_digital_twin import save_result, simulate


def _factory() -> dict[str, object]:
    return {
        "factory_id": "sylvapapers-module-a-test",
        "machine_types": [
            {
                "machine_type": "paper_machine",
                "failure_density": {
                    "family": "weibull",
                    "shape": 2.0,
                    "scale_hours": 0.01,
                },
            }
        ],
        "machines": [
            {
                "machine_id": "paper-machine-01",
                "name": "Machine à papier",
                "machine_type": "paper_machine",
                "metadata": {
                    "processing_time": 10,
                    "repair_time": 7,
                    "maintenance_recovery": 0.5,
                    "preventive_interval_hours": 0.05,
                    "preventive_maintenance_duration_minutes": 3,
                    "preventive_maintenance_recovery": 1.0,
                    "energy_kw": 100,
                },
            }
        ],
        "process_graph": {
            "nodes": [
                {
                    "node_id": "paper-machine",
                    "kind": "operation",
                    "machine_ids": ["paper-machine-01"],
                }
            ],
            "edges": [],
        },
    }


def _scenario() -> dict[str, object]:
    return {
        "scenario_id": "module-a-output-contract",
        "start_at": "2026-09-07T06:00:00+02:00",
        "random_seed": 91,
        "orders": [
            {
                "order_id": "ROLL",
                "product_id": "kraft-roll",
                "quantity": 2,
                "due_at": 100,
            }
        ],
    }


def test_detailed_module_a_outputs_are_deterministic_and_ready_for_module_b() -> None:
    first = simulate(_factory(), _scenario())
    second = simulate(_factory(), _scenario())

    assert first.sensor_records == second.sensor_records
    assert first.machine_states == second.machine_states
    assert first.failure_events == second.failure_events
    assert first.maintenance_interventions == second.maintenance_interventions
    assert first.queue_history == second.queue_history
    assert first.work_in_progress == second.work_in_progress
    assert first.final_state == second.final_state

    sensor = first.sensor_records[0]
    assert sensor["machine_id"] == "paper-machine-01"
    assert {
        "temperature_c",
        "vibration_mm_s",
        "pressure_bar",
        "power_kw",
        "operating_age_hours",
        "degradation_index",
        "failure_probability",
    } <= sensor.keys()
    assert sensor["synthetic"] is True

    statuses = {row["status"] for row in first.machine_states}
    assert {"idle", "maintenance", "failed", "running"} <= statuses
    assert {row["maintenance_type"] for row in first.maintenance_interventions} == {
        "corrective",
        "preventive",
    }
    assert all(row["failure_mode"] == "weibull_ageing" for row in first.failure_events)
    assert first.final_state["work_in_progress"] == 0
    assert first.final_state["totals"]["estimated_emissions_kg_co2e"] > 0
    assert first.metadata["model_limits"]["resource_calendars"] == "declared_not_enforced"


def test_detailed_exchange_bundle_is_persisted(tmp_path: Path) -> None:
    result = simulate(_factory(), _scenario())
    save_result(result, tmp_path, plots=False)

    filenames = {
        "machine_states.csv",
        "sensors.csv",
        "failures.csv",
        "maintenance.csv",
        "queues.csv",
        "work_in_progress.csv",
        "final_state.json",
    }
    assert filenames <= {path.name for path in tmp_path.iterdir()}
    with (tmp_path / "sensors.csv").open(encoding="utf-8", newline="") as stream:
        sensor_rows = list(csv.DictReader(stream))
    assert len(sensor_rows) == len(result.sensor_records)
    assert sensor_rows[0]["vibration_mm_s"]
    final_state = json.loads((tmp_path / "final_state.json").read_text(encoding="utf-8"))
    assert final_state["work_in_progress"] == 0
