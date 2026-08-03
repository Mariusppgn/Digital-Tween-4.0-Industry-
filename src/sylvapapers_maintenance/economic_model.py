"""Cost-sensitive machine learning for lost-revenue maintenance priorities."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import matplotlib
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.style.use("ggplot")

FEATURE_COLUMNS = (
    "operating_hours",
    "utilization_rate",
    "hourly_operating_cost",
    "hourly_idle_cost",
    "expected_repair_hours",
    "weibull_shape",
    "weibull_scale_hours",
    "topology_loss_fraction",
    "nominal_revenue_exposure_per_hour",
)
TARGET_COLUMN = "lost_revenue_due_to_failures"


@dataclass(frozen=True)
class EconomicModelResult:
    """Trained model plus leakage-controlled holdout evidence."""

    model: ExtraTreesRegressor
    metrics: dict[str, Any]
    predictions: list[dict[str, Any]]
    priorities: list[dict[str, Any]]
    feature_importance: list[dict[str, Any]]


def _float(row: dict[str, str], name: str) -> float:
    value = row.get(name, "")
    return float(value) if value not in {"", None} else 0.0


def _matrix(rows: list[dict[str, str]]) -> np.ndarray[Any, np.dtype[np.float64]]:
    return np.asarray(
        [[_float(row, column) for column in FEATURE_COLUMNS] for row in rows],
        dtype=float,
    )


def _weights(
    target: np.ndarray[Any, np.dtype[np.float64]],
) -> np.ndarray[Any, np.dtype[np.float64]]:
    positive = target[target > 0]
    scale = float(np.mean(positive)) if positive.size else 1.0
    return 1 + np.minimum(target / max(scale, 1e-9), 10)


def train_lost_revenue_model(
    input_csv: str | Path,
    *,
    validation_fraction: float = 0.2,
    preventive_cost: float = 3_000,
    predictive_effectiveness: float = 0.75,
) -> EconomicModelResult:
    """Train on earlier replications and validate on later unseen seeds."""

    source = Path(input_csv)
    with source.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) < 20:
        raise ValueError("At least 20 machine-replication rows are required")
    if not 0.1 <= validation_fraction <= 0.5:
        raise ValueError("validation_fraction must be between 0.1 and 0.5")
    replications = sorted({int(row["replication"]) for row in rows})
    validation_count = max(1, round(len(replications) * validation_fraction))
    validation_replications = set(replications[-validation_count:])
    training_rows = [row for row in rows if int(row["replication"]) not in validation_replications]
    validation_rows = [row for row in rows if int(row["replication"]) in validation_replications]
    x_train = _matrix(training_rows)
    x_validation = _matrix(validation_rows)
    y_train = np.asarray([_float(row, TARGET_COLUMN) for row in training_rows], dtype=float)
    y_validation = np.asarray([_float(row, TARGET_COLUMN) for row in validation_rows], dtype=float)
    if not np.any(y_train > 0):
        raise ValueError("Training data contain no positive lost-revenue event")

    model = ExtraTreesRegressor(
        n_estimators=400,
        min_samples_leaf=10,
        max_features=0.8,
        random_state=42,
        n_jobs=1,
    )
    model.fit(x_train, y_train)
    predicted = np.maximum(0, model.predict(x_validation))
    validation_weights = _weights(y_validation)
    selected = predicted * predictive_effectiveness > preventive_cost
    policy_net_avoided = float(
        np.sum(
            np.where(
                selected,
                y_validation * predictive_effectiveness - preventive_cost,
                0,
            )
        )
    )
    score = (
        float(r2_score(y_validation, predicted))
        if len(y_validation) > 1 and float(np.var(y_validation)) > 0
        else None
    )
    metrics = {
        "model_type": "ExtraTreesRegressor_expected_lost_revenue",
        "training_rows": len(training_rows),
        "validation_rows": len(validation_rows),
        "training_replications": len(replications) - validation_count,
        "validation_replications": validation_count,
        "positive_training_rows": int(np.sum(y_train > 0)),
        "positive_validation_rows": int(np.sum(y_validation > 0)),
        "mean_absolute_error": round(float(mean_absolute_error(y_validation, predicted)), 6),
        "weighted_mean_absolute_error": round(
            float(mean_absolute_error(y_validation, predicted, sample_weight=validation_weights)),
            6,
        ),
        "root_mean_squared_error": round(
            float(mean_squared_error(y_validation, predicted) ** 0.5), 6
        ),
        "r2_score": round(score, 6) if score is not None else None,
        "baseline_lost_revenue": round(float(np.sum(y_validation)), 6),
        "policy_selected_rows": int(np.sum(selected)),
        "policy_net_avoided_loss": round(policy_net_avoided, 6),
        "preventive_cost": preventive_cost,
        "predictive_effectiveness": predictive_effectiveness,
        "currency": "EUR",
        "split_method": "ordered_replication_holdout_no_random_seed_leakage",
        "limitations": [
            "Training labels are synthetic failure consequences, not observed accounting losses.",
            "The policy estimate assumes the configured predictive effectiveness and intervention cost.",
            "The model ranks economic exposure; it does not actuate equipment or create work orders.",
        ],
    }
    prediction_rows: list[dict[str, Any]] = []
    for row, actual, estimate, recommend in zip(
        validation_rows, y_validation, predicted, selected, strict=True
    ):
        prediction_rows.append(
            {
                "schema_version": "1.0.0",
                "producer_version": "0.5.0",
                "replication": int(row["replication"]),
                "seed": int(row["seed"]),
                "machine_id": row["machine_id"],
                "process_node_id": row["process_node_id"],
                "actual_lost_revenue": round(float(actual), 6),
                "predicted_lost_revenue": round(float(estimate), 6),
                "recommended_predictive_intervention": bool(recommend),
                "expected_net_benefit": round(
                    float(estimate) * predictive_effectiveness - preventive_cost, 6
                ),
                "currency": "EUR",
                "data_classification": "synthetic_hypothesis_not_calibrated",
                "provenance": "module_b_cost_sensitive_economic_model",
            }
        )

    by_machine: dict[str, list[dict[str, Any]]] = {}
    for row in prediction_rows:
        by_machine.setdefault(str(row["machine_id"]), []).append(row)
    priorities = []
    for machine_id, machine_rows in sorted(by_machine.items()):
        predicted_mean = float(np.mean([row["predicted_lost_revenue"] for row in machine_rows]))
        priorities.append(
            {
                "machine_id": machine_id,
                "process_node_id": machine_rows[0]["process_node_id"],
                "predicted_lost_revenue_mean": round(predicted_mean, 6),
                "recommended_predictive_intervention": (
                    predicted_mean * predictive_effectiveness > preventive_cost
                ),
                "expected_net_benefit": round(
                    predicted_mean * predictive_effectiveness - preventive_cost, 6
                ),
                "validation_observations": len(machine_rows),
                "currency": "EUR",
            }
        )
    priorities.sort(key=lambda row: float(row["predicted_lost_revenue_mean"]), reverse=True)
    for rank, row in enumerate(priorities, 1):
        row["economic_priority_rank"] = rank

    permutation = permutation_importance(
        model,
        x_validation,
        y_validation,
        scoring="neg_mean_absolute_error",
        n_repeats=5,
        random_state=42,
    )
    importance = [
        {
            "feature": feature,
            "importance_mean": round(float(mean), 9),
            "importance_standard_deviation": round(float(deviation), 9),
        }
        for feature, mean, deviation in zip(
            FEATURE_COLUMNS,
            permutation.importances_mean,
            permutation.importances_std,
            strict=True,
        )
    ]
    importance.sort(key=lambda row: float(str(row["importance_mean"])), reverse=True)
    return EconomicModelResult(model, metrics, prediction_rows, priorities, importance)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def save_lost_revenue_model(
    result: EconomicModelResult,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Persist the model, evidence, priorities and a ggplot validation figure."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "model": output / "lost_revenue_model.joblib",
        "metrics": output / "economic_model_metrics.json",
        "predictions": output / "economic_model_predictions.csv",
        "priorities": output / "machine_economic_priorities.csv",
        "feature_importance": output / "economic_model_feature_importance.csv",
        "plot": output / "economic_model_validation.png",
        "manifest": output / "economic_model_manifest.json",
    }
    joblib.dump(result.model, paths["model"])
    paths["metrics"].write_text(
        json.dumps(result.metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    _write_csv(paths["predictions"], result.predictions)
    _write_csv(paths["priorities"], result.priorities)
    _write_csv(paths["feature_importance"], result.feature_importance)

    actual = [float(row["actual_lost_revenue"]) for row in result.predictions]
    predicted = [float(row["predicted_lost_revenue"]) for row in result.predictions]
    figure, axis = plt.subplots(figsize=(7, 6))
    axis.scatter(actual, predicted, alpha=0.55)
    upper = max(actual + predicted + [1.0])
    axis.plot([0, upper], [0, upper], linestyle="--", label="Prédiction parfaite")
    axis.set(
        title="Validation du modèle de manque à gagner",
        xlabel="Manque à gagner simulé (EUR)",
        ylabel="Manque à gagner prédit (EUR)",
    )
    axis.legend()
    figure.tight_layout()
    figure.savefig(paths["plot"], dpi=150)
    plt.close(figure)

    model_hash = hashlib.sha256(paths["model"].read_bytes()).hexdigest()
    manifest = {
        "schema_version": "1.0.0",
        "producer_version": "0.5.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "model_type": result.metrics["model_type"],
        "features": list(FEATURE_COLUMNS),
        "target": TARGET_COLUMN,
        "model_sha256": model_hash,
        "security": (
            "joblib uses pickle semantics; load only this trusted local artifact after hash validation"
        ),
        "data_classification": "synthetic_hypothesis_not_calibrated",
        "intended_use": "maintenance_priority_decision_support_only",
        "files": {name: path.name for name, path in paths.items() if name != "manifest"},
    }
    paths["manifest"].write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return paths
