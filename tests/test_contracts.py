from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from asteria_contracts import (
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
        product_id="panel-a",
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
            product_id="panel-a",
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
    assert len(paths) == 19
    assert all(path.read_text(encoding="utf-8").startswith("{") for path in paths)
