"""Reliability functions shared by the simulator and factory editor."""

from __future__ import annotations

import math


def weibull_density(
    operating_age_hours: float,
    *,
    shape: float,
    scale_hours: float,
) -> float:
    """Return the Weibull probability density at an equipment operating age."""
    if shape <= 0 or scale_hours <= 0:
        raise ValueError("shape and scale_hours must be strictly positive")
    if operating_age_hours < 0:
        raise ValueError("operating age must be non-negative")
    if operating_age_hours == 0:
        if shape < 1:
            return math.inf
        if shape == 1:
            return 1 / scale_hours
        return 0.0
    ratio = operating_age_hours / scale_hours
    return float((shape / scale_hours) * ratio ** (shape - 1) * math.exp(-(ratio**shape)))


def weibull_cdf(
    operating_age_hours: float,
    *,
    shape: float,
    scale_hours: float,
) -> float:
    """Return the Weibull cumulative failure probability at an operating age."""
    if shape <= 0 or scale_hours <= 0:
        raise ValueError("shape and scale_hours must be strictly positive")
    if operating_age_hours < 0:
        raise ValueError("operating age must be non-negative")
    if operating_age_hours == 0:
        return 0.0
    return 1 - math.exp(-((operating_age_hours / scale_hours) ** shape))


def conditional_failure_probability(
    operating_age_hours: float,
    interval_hours: float,
    *,
    shape: float,
    scale_hours: float,
) -> float:
    """Return P(failure in the interval | survived to the current age)."""
    if operating_age_hours < 0 or interval_hours < 0:
        raise ValueError("operating age and interval must be non-negative")
    if shape <= 0 or scale_hours <= 0:
        raise ValueError("shape and scale_hours must be strictly positive")
    if interval_hours == 0:
        return 0.0
    start = operating_age_hours
    end = operating_age_hours + interval_hours
    cumulative_hazard = (end / scale_hours) ** shape - (start / scale_hours) ** shape
    return max(0.0, min(1.0, 1 - math.exp(-cumulative_hazard)))
