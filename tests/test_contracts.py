from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from sylvapapers_contracts import (
    DemandForecast,
    ForecastPoint,
    ProcessEdge,
    ProcessGraph,
    ProcessNode,
    RDPortfolio,
    RDProject,
    SensorRecord,
    SimulationScenario,
    export_json_schemas,
)
from sylvapapers_contracts.models import FactoryConfig, FailureDensityConfig, ProductDefinition

NOW = datetime(2026, 9, 7, tzinfo=UTC)


def test_graph_rejects_dangling_edge() -> None:
    with pytest.raises(ValidationError, match="existing nodes"):
        ProcessGraph(
            nodes=[
                ProcessNode(node_id="source", kind="source", name="Source"),
                ProcessNode(node_id="sink", kind="sink", name="Sink"),
            ],
            edges=[ProcessEdge(source="source", target="missing")],
        )


def test_sensor_record_requires_units_for_every_value() -> None:
    with pytest.raises(ValidationError, match="exactly one unit"):
        SensorRecord(
            sensor_id="oven-temperature",
            machine_id="oven-01",
            timestamp=NOW,
            values={"temperature": 180.0, "pressure": 6.2},
            units={"temperature": "degC"},
        )


def test_forecast_quantiles_are_ordered() -> None:
    point = ForecastPoint(
        period_start=NOW,
        product_id="paper-roll-a",
        p10=10,
        p50=15,
        p90=20,
    )
    forecast = DemandForecast(
        forecast_id="forecast-01",
        generated_at=NOW,
        horizon="weekly",
        method="expert_baseline",
        points=[point],
    )
    assert forecast.points[0].p50 == 15

    with pytest.raises(ValidationError, match="p10 <= p50 <= p90"):
        ForecastPoint(
            period_start=NOW,
            product_id="paper-roll-a",
            p10=20,
            p50=15,
            p90=10,
        )


def test_rd_portfolio_enforces_budget_limit() -> None:
    project = RDProject(
        project_id="rd-01",
        name="Fast cure resin",
        stage="prototype",
        budget=120_000,
        start_at=NOW,
        target_end_at=NOW + timedelta(days=180),
        technology_readiness_level=5,
        expected_value=250_000,
    )
    with pytest.raises(ValidationError, match="budget"):
        RDPortfolio(
            portfolio_id="portfolio-01",
            name="Materials 2027",
            budget_limit=100_000,
            projects=[project],
        )


def test_scenario_rejects_order_for_unknown_product() -> None:
    with pytest.raises(ValidationError, match="unknown products"):
        SimulationScenario.model_validate(
            {
                "scenario_id": "bad",
                "name": "Bad reference",
                "factory_id": "factory",
                "start_at": NOW,
                "end_at": NOW + timedelta(days=1),
                "products": [
                    {
                        "product_id": "known",
                        "name": "Known",
                        "routing": ["cut"],
                    }
                ],
                "orders": [
                    {
                        "order_id": "o1",
                        "product_id": "unknown",
                        "quantity": 1,
                        "release_at": NOW,
                        "due_at": NOW + timedelta(hours=1),
                    }
                ],
            }
        )


def test_all_public_contracts_export_json_schema(tmp_path) -> None:
    paths = export_json_schemas(tmp_path)
    assert len(paths) == 21
    assert all(path.read_text(encoding="utf-8").startswith("{") for path in paths)


def test_weibull_failure_density_is_evaluable() -> None:
    density = FailureDensityConfig(shape=2, scale_hours=100)

    assert density.density_at(0) == 0
    assert density.density_at(100) == pytest.approx(2 / 100 * 2.718281828459045**-1)
    with pytest.raises(ValueError, match="non-negative"):
        density.density_at(-1)
    with pytest.raises(ValidationError, match="location_hours"):
        FailureDensityConfig.model_validate({"shape": 2, "scale_hours": 100, "location_hours": 10})


def test_product_routing_can_be_derived_from_edited_graph() -> None:
    product = ProductDefinition(product_id="paper-roll", name="Paper roll")

    assert product.enabled is True
    assert product.routing == []


def test_factory_rejects_machine_with_undeclared_type() -> None:
    with pytest.raises(ValidationError, match="unknown machine types"):
        FactoryConfig.model_validate(
            {
                "factory_id": "paper-mill",
                "name": "Paper mill",
                "machine_types": [
                    {
                        "machine_type": "dryer",
                        "name": "Dryer",
                        "failure_density": {"shape": 2, "scale_hours": 1000},
                    }
                ],
                "machines": [
                    {
                        "machine_id": "press-01",
                        "name": "Press",
                        "machine_type": "press",
                        "capabilities": ["pressing"],
                        "capacity_per_hour": 1,
                    }
                ],
                "process_graph": {
                    "nodes": [
                        {"node_id": "source", "kind": "source", "name": "Source"},
                        {
                            "node_id": "pressing",
                            "kind": "operation",
                            "name": "Pressing",
                            "machine_ids": ["press-01"],
                        },
                        {"node_id": "sink", "kind": "sink", "name": "Sink"},
                    ],
                    "edges": [
                        {"source": "source", "target": "pressing"},
                        {"source": "pressing", "target": "sink"},
                    ],
                },
            }
        )


def test_scenario_rejects_order_for_disabled_product() -> None:
    with pytest.raises(ValidationError, match="disabled products"):
        SimulationScenario.model_validate(
            {
                "scenario_id": "disabled-product-order",
                "name": "Disabled product order",
                "factory_id": "paper-mill",
                "start_at": NOW,
                "end_at": NOW + timedelta(days=1),
                "products": [
                    {
                        "product_id": "inactive-roll",
                        "name": "Inactive roll",
                        "enabled": False,
                        "routing": ["winding"],
                    }
                ],
                "orders": [
                    {
                        "order_id": "order-1",
                        "product_id": "inactive-roll",
                        "quantity": 1,
                        "release_at": NOW,
                        "due_at": NOW + timedelta(hours=1),
                    }
                ],
            }
        )
