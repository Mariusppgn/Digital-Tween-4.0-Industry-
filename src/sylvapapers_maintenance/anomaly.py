"""Fast and explainable anomaly detection for paper-mill sensor records."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict

from sylvapapers_contracts import AnomalyResult, MaintenanceAnalysisConfig, SensorRecord


def _robust_scale(values: list[float]) -> tuple[float, float]:
    center = statistics.median(values)
    mad = statistics.median(abs(value - center) for value in values)
    scale = 1.4826 * mad
    if scale <= 1e-12 and len(values) > 1:
        scale = statistics.pstdev(values)
    # A perfectly flat baseline is common for synthetic ratios. A 1% physical
    # floor avoids meaningless scores in the millions while still detecting a
    # material departure from the reference regime.
    return center, max(scale, abs(center) * 0.01, 1e-3)


def _normalised_importance(scores: dict[str, float]) -> dict[str, float]:
    total = sum(scores.values())
    if total <= 0:
        return {name: 0.0 for name in sorted(scores)}
    return {name: round(value / total, 8) for name, value in sorted(scores.items())}


def ewma_robust_anomaly(
    records: list[SensorRecord],
    config: MaintenanceAnalysisConfig,
) -> AnomalyResult:
    """Score the latest record using EWMA residuals and median absolute deviation.

    Bad-quality points are excluded. The baseline uses the earliest configured
    number of observations, which keeps the result deterministic and avoids
    contaminating the reference window with future values.
    """

    usable = sorted(
        (record for record in records if record.quality != "bad"),
        key=lambda record: (record.timestamp, record.sensor_id),
    )
    if not usable:
        raise ValueError("at least one non-bad SensorRecord is required")
    machine_ids = {record.machine_id for record in usable}
    if len(machine_ids) != 1:
        raise ValueError("EWMA anomaly analysis accepts records for exactly one machine")

    by_variable: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for index, record in enumerate(usable):
        for name, value in record.values.items():
            if math.isfinite(value):
                by_variable[name].append((index, value))

    latest_index = len(usable) - 1
    scores: dict[str, float] = {}
    for name, observations in by_variable.items():
        values = [value for _, value in observations]
        baseline_size = min(len(values), config.minimum_baseline_points)
        center, scale = _robust_scale(values[:baseline_size])
        ewma = center
        latest_score = 0.0
        for record_index, value in observations:
            residual = abs(value - ewma) / scale
            ewma = config.ewma_alpha * value + (1 - config.ewma_alpha) * ewma
            if record_index == latest_index:
                latest_score = residual
        scores[name] = latest_score

    score = max(scores.values(), default=0.0)
    return AnomalyResult(
        machine_id=next(iter(machine_ids)),
        assessed_at=usable[-1].timestamp,
        score=score,
        threshold=config.robust_z_threshold,
        is_anomaly=score >= config.robust_z_threshold,
        observations_used=len(usable),
        variable_importance=_normalised_importance(scores),
        provenance="module_b",
    )
