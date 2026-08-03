from __future__ import annotations

import pytest

from sylvapapers_digital_twin.economics import EconomicTopologyModel


def _model() -> EconomicTopologyModel:
    factory = {
        "machines": [
            {"machine_id": "common", "capacity_per_hour": 10, "hourly_idle_cost": 20},
            {"machine_id": "kraft_1", "capacity_per_hour": 6, "hourly_idle_cost": 10},
            {"machine_id": "kraft_2", "capacity_per_hour": 4, "hourly_idle_cost": 10},
            {"machine_id": "print", "capacity_per_hour": 10, "hourly_idle_cost": 10},
        ],
        "process_graph": {
            "nodes": [
                {"node_id": "common_node", "machine_ids": ["common"]},
                {"node_id": "kraft_node", "machine_ids": ["kraft_1", "kraft_2"]},
                {"node_id": "print_node", "machine_ids": ["print"]},
            ]
        },
    }
    scenario = {
        "start_at": "2026-01-01T00:00:00",
        "interarrival_time": 60,
        "orders": [
            {"product_id": "kraft", "quantity": 3},
            {"product_id": "printing", "quantity": 1},
        ],
        "economics": {"currency": "EUR"},
    }
    products = {
        "kraft": {
            "enabled": True,
            "sale_price_per_unit": 100,
            "routing": ["common_node", "kraft_node"],
        },
        "printing": {
            "enabled": True,
            "sale_price_per_unit": 100,
            "routing": ["common_node", "print_node"],
        },
    }
    return EconomicTopologyModel(factory, scenario, products)


def test_series_and_branching_losses_follow_fixed_capacity_shares() -> None:
    model = _model()

    assert model.topology_loss_fraction("common_node", "common") == pytest.approx(1)
    assert model.topology_loss_fraction("print_node", "print") == pytest.approx(0.25)
    assert model.topology_loss_fraction("kraft_node", "kraft_1") == pytest.approx(0.45)
    assert model.topology_loss_fraction("kraft_node", "kraft_2") == pytest.approx(0.30)


def test_failure_impact_does_not_credit_catch_up_capacity() -> None:
    model = _model()

    impact = model.failure_impact(
        failure_id="F-1",
        machine_id="kraft_1",
        process_node_id="kraft_node",
        time_minutes=60,
        downtime_minutes=120,
    )

    assert impact["method"] == "fixed_nominal_capacity_no_catch_up"
    assert impact["nominal_factory_revenue_per_hour"] == pytest.approx(100)
    assert impact["estimated_lost_revenue"] == pytest.approx(90)
    assert impact["unavoidable_machine_cost"] == pytest.approx(20)


def test_revenue_ledger_is_monotonic_and_counterfactual() -> None:
    model = _model()
    observations = model.revenue_observations(
        [
            {"product_id": "kraft", "accepted": True, "completion_time": 30},
            {"product_id": "printing", "accepted": True, "completion_time": 90},
        ],
        [],
        [
            model.failure_impact(
                failure_id="F-1",
                machine_id="print",
                process_node_id="print_node",
                time_minutes=0,
                downtime_minutes=60,
            )
        ],
    )

    assert [row["cumulative_revenue"] for row in observations] == [100, 200]
    assert observations[-1]["counterfactual_cumulative_revenue"] == pytest.approx(225)
    assert observations[-1]["cumulative_failure_lost_revenue"] == pytest.approx(25)
