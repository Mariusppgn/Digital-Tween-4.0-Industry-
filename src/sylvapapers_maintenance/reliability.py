"""Conditional Weibull risk and lightweight remaining-life estimates."""

from __future__ import annotations

import math
from datetime import datetime

from sylvapapers_contracts import FailureDensityConfig, ReliabilityEstimate


def conditional_weibull_probability(
    operating_age_hours: float,
    horizon_hours: float,
    density: FailureDensityConfig,
) -> float:
    """Return failure probability over a horizon conditional on current survival."""

    if not math.isfinite(operating_age_hours) or operating_age_hours < 0:
        raise ValueError("operating_age_hours must be finite and non-negative")
    if not math.isfinite(horizon_hours) or horizon_hours <= 0:
        raise ValueError("horizon_hours must be finite and strictly positive")
    start_hazard = (operating_age_hours / density.scale_hours) ** density.shape
    end_hazard = ((operating_age_hours + horizon_hours) / density.scale_hours) ** density.shape
    return max(0.0, min(1.0, 1 - math.exp(-(end_hazard - start_hazard))))


def conditional_weibull_quantile(
    probability: float,
    operating_age_hours: float,
    density: FailureDensityConfig,
) -> float:
    """Return a conditional time-to-failure quantile in operating hours."""

    if not 0 < probability < 1:
        raise ValueError("probability must be strictly between zero and one")
    if not math.isfinite(operating_age_hours) or operating_age_hours < 0:
        raise ValueError("operating_age_hours must be finite and non-negative")
    current_hazard = (operating_age_hours / density.scale_hours) ** density.shape
    failure_age = density.scale_hours * (current_hazard - math.log1p(-probability)) ** (
        1 / density.shape
    )
    return float(max(0.0, failure_age - operating_age_hours))


def estimate_reliability(
    *,
    machine_id: str,
    assessed_at: datetime,
    operating_age_hours: float,
    horizon_hours: float,
    density: FailureDensityConfig,
    confidence_level: float,
    evidence_points: int,
) -> ReliabilityEstimate:
    """Build an interpretable risk and RUL estimate from a two-parameter Weibull."""

    if evidence_points < 0:
        raise ValueError("evidence_points must be non-negative")
    tail = (1 - confidence_level) / 2
    evidence_confidence = min(confidence_level, evidence_points / 30)
    return ReliabilityEstimate(
        machine_id=machine_id,
        assessed_at=assessed_at,
        operating_age_hours=operating_age_hours,
        horizon_hours=horizon_hours,
        failure_probability=conditional_weibull_probability(
            operating_age_hours, horizon_hours, density
        ),
        rul_hours=conditional_weibull_quantile(0.5, operating_age_hours, density),
        rul_lower_hours=conditional_weibull_quantile(tail, operating_age_hours, density),
        rul_upper_hours=conditional_weibull_quantile(1 - tail, operating_age_hours, density),
        confidence=evidence_confidence,
        provenance="module_b",
    )
