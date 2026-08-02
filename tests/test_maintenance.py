from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from sylvapapers_contracts import (
    FailureDensityConfig,
    MaintenanceAnalysisConfig,
    ProductionOrder,
    SensorRecord,
)
from sylvapapers_maintenance import (
    analyze_maintenance_bundle,
    conditional_weibull_probability,
    conditional_weibull_quantile,
    ewma_robust_anomaly,
    load_module_a_outputs,
    save_maintenance_analysis,
)

NOW = datetime(2026, 1, 5, tzinfo=UTC)
ROOT = Path(__file__).parents[1]


def _sensor(value: float, minute: int) -> SensorRecord:
    return SensorRecord(
        sensor_id="dryer-sensor",
        machine_id="dryer-01",
        timestamp=NOW.replace(minute=minute),
        values={"vibration_mm_s": value},
        units={"vibration_mm_s": "mm/s"},
    )


def test_robust_ewma_detects_and_explains_latest_spike() -> None:
    records = [_sensor(value, minute) for minute, value in enumerate([2, 2.1, 1.9, 2, 2.05, 8])]
    result = ewma_robust_anomaly(records, MaintenanceAnalysisConfig())

    assert result.is_anomaly is True
    assert result.score > result.threshold
    assert result.variable_importance == {"vibration_mm_s": 1.0}


def test_conditional_weibull_risk_and_rul_are_monotonic() -> None:
    density = FailureDensityConfig(shape=2.5, scale_hours=1_000)
    young = conditional_weibull_probability(100, 72, density)
    old = conditional_weibull_probability(800, 72, density)

    assert 0 < young < old < 1
    assert conditional_weibull_quantile(0.1, 800, density) < conditional_weibull_quantile(
        0.9, 800, density
    )


def test_module_a_bundle_produces_contracts_costs_and_figures(tmp_path: Path) -> None:
    input_dir = ROOT / "data" / "examples" / "maintenance"
    dataset = load_module_a_outputs(input_dir)
    result = analyze_maintenance_bundle(
        input_dir,
        ROOT / "configs" / "maintenance" / "baseline.yaml",
    )
    paths = save_maintenance_analysis(result, tmp_path)

    assert len(result.assessments) == 1
    assert len(dataset.maintenance_interventions) == 1
    assessment = result.assessments[0]
    assert assessment.machine_id == "dryer-01"
    assert assessment.anomaly.is_anomaly is True
    assert assessment.recommendation.policy == "predictive"
    assert {row.policy for row in assessment.policy_comparison} == {
        "corrective",
        "preventive",
        "predictive",
    }
    assert len(paths) == 5
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths.values())


def test_quantity_and_non_finite_values_are_rejected() -> None:
    with pytest.raises(ValidationError):
        ProductionOrder(
            order_id="oversized",
            product_id="kraft-roll",
            quantity=100_001,
            release_at=NOW,
            due_at=NOW.replace(day=6),
        )
    with pytest.raises(ValidationError):
        MaintenanceAnalysisConfig(horizon_hours=float("inf"))
