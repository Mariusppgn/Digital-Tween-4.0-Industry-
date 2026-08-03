from __future__ import annotations

import csv
from pathlib import Path

from sylvapapers_maintenance import save_lost_revenue_model, train_lost_revenue_model


def _dataset(path: Path) -> None:
    fields = [
        "replication",
        "seed",
        "machine_id",
        "process_node_id",
        "operating_hours",
        "utilization_rate",
        "hourly_operating_cost",
        "hourly_idle_cost",
        "expected_repair_hours",
        "weibull_shape",
        "weibull_scale_hours",
        "topology_loss_fraction",
        "nominal_revenue_exposure_per_hour",
        "lost_revenue_due_to_failures",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for replication in range(1, 11):
            for machine_index in range(4):
                exposure = 1_000 * (machine_index + 1)
                writer.writerow(
                    {
                        "replication": replication,
                        "seed": 1000 + replication,
                        "machine_id": f"M-{machine_index}",
                        "process_node_id": f"N-{machine_index}",
                        "operating_hours": 100 + replication,
                        "utilization_rate": 0.5 + machine_index / 10,
                        "hourly_operating_cost": 100 + 10 * machine_index,
                        "hourly_idle_cost": 20 + machine_index,
                        "expected_repair_hours": 1 + machine_index / 2,
                        "weibull_shape": 2,
                        "weibull_scale_hours": 500 - 20 * machine_index,
                        "topology_loss_fraction": 0.25 * (machine_index + 1),
                        "nominal_revenue_exposure_per_hour": exposure,
                        "lost_revenue_due_to_failures": (
                            exposure * 2 if (replication + machine_index) % 3 == 0 else 0
                        ),
                    }
                )


def test_economic_model_uses_ordered_holdout_and_exports_ggplot(tmp_path: Path) -> None:
    dataset = tmp_path / "machines.csv"
    _dataset(dataset)

    result = train_lost_revenue_model(dataset)
    paths = save_lost_revenue_model(result, tmp_path / "model")

    assert result.metrics["training_replications"] == 8
    assert result.metrics["validation_replications"] == 2
    assert result.metrics["split_method"] == "ordered_replication_holdout_no_random_seed_leakage"
    assert len(result.predictions) == 8
    assert result.priorities[0]["economic_priority_rank"] == 1
    assert all(path.stat().st_size > 0 for path in paths.values())
