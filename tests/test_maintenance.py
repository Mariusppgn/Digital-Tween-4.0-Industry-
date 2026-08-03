from __future__ import annotations

import csv
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from sylvapapers_contracts import (
    FailureDensityConfig,
    FailureEvent,
    MaintenanceAnalysisConfig,
    ProductionOrder,
    SensorRecord,
)
from sylvapapers_maintenance import (
    analyze_maintenance_bundle,
    backtest_temporal_alerts,
    conditional_weibull_probability,
    conditional_weibull_quantile,
    cusum_robust_anomaly,
    ewma_robust_anomaly,
    load_module_a_outputs,
    save_maintenance_analysis,
)
from sylvapapers_maintenance.io import MaintenanceDataset

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


def test_robust_cusum_detects_persistent_shift() -> None:
    records = [
        SensorRecord(
            sensor_id="dryer-sensor",
            machine_id="dryer-01",
            timestamp=NOW + timedelta(hours=index),
            values={"vibration_mm_s": value},
            units={"vibration_mm_s": "mm/s"},
        )
        for index, value in enumerate([2, 2, 2, 2, 2, 2.4, 2.5, 2.6])
    ]
    result = cusum_robust_anomaly(records, MaintenanceAnalysisConfig())

    assert result.method == "cusum_robust"
    assert result.is_anomaly is True
    assert result.score >= result.threshold


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
    assert len(paths) == 13
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths.values())
    with paths["machine_decision_features"].open(encoding="utf-8", newline="") as stream:
        row = next(csv.DictReader(stream))
    assert row["schema_version"] == "1.0.0"
    assert row["provenance"] == "module_b_decision_features"
    assert row["probability_unit"] == "ratio"
    assert row["time_unit"] == "operating_hour"
    assert 0 <= float(row["capacity_loss_ratio"]) <= 1
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["intended_consumers"] == ["module_c", "module_d", "module_e"]
    assert manifest["flat_exports"]["machine_decision_features"] == (
        "machine_decision_features.csv"
    )
    assert manifest["analysis_reference_at"] == assessment.created_at.isoformat()
    assert manifest["generated_at"] != manifest["analysis_reference_at"]


def test_temporal_backtest_is_censored_and_does_not_use_future_features() -> None:
    records = [
        SensorRecord(
            sensor_id="dryer-sensor",
            machine_id="dryer-01",
            timestamp=NOW + timedelta(hours=index),
            values={
                "vibration_mm_s": value,
                "operating_age_hours": 100 + index,
            },
            units={"vibration_mm_s": "mm/s", "operating_age_hours": "h"},
        )
        for index, value in enumerate([2, 2, 2, 2, 2, 2.5, 2.6, 2.7, 2.8, 2.8, 2.8, 2.8, 2.8])
    ]
    failure = FailureEvent(
        failure_id="failure-001",
        machine_id="dryer-01",
        occurred_at=NOW + timedelta(hours=9),
        failure_mode="bearing",
        severity=3,
        downtime_minutes=120,
    )
    config = MaintenanceAnalysisConfig(horizon_hours=3, minimum_baseline_points=5)
    result = backtest_temporal_alerts(
        MaintenanceDataset(sensor_records=records, failure_events=[failure]),
        config,
    )

    assert {item.method for item in result.metrics} == {
        "ewma_robust",
        "cusum_robust",
    }
    assert all(item.true_positive > 0 for item in result.metrics)
    assert all(item.censored_points > 0 for item in result.metrics)
    assert all(item.detected_failure_events == 1 for item in result.metrics)
    assert result.calibration_bins

    prefix_cutoff = NOW + timedelta(hours=6)
    original = next(
        item
        for item in result.predictions
        if item.method == "ewma_robust" and item.assessed_at == prefix_cutoff
    )
    altered_records = [*records]
    altered_records[-1] = altered_records[-1].model_copy(
        update={"values": {"vibration_mm_s": 999, "operating_age_hours": 112}}
    )
    altered = backtest_temporal_alerts(
        MaintenanceDataset(sensor_records=altered_records, failure_events=[failure]),
        config,
    )
    same_time = next(
        item
        for item in altered.predictions
        if item.method == "ewma_robust" and item.assessed_at == prefix_cutoff
    )
    assert same_time.anomaly_score == original.anomaly_score


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
