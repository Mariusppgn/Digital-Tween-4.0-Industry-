import math

import pytest

from sylvapapers_digital_twin import simulate
from sylvapapers_digital_twin.reliability import (
    conditional_failure_probability,
    weibull_cdf,
    weibull_density,
)


def test_weibull_density_and_cdf_match_exponential_when_shape_is_one() -> None:
    density = weibull_density(10, shape=1, scale_hours=10)
    cumulative = weibull_cdf(10, shape=1, scale_hours=10)

    assert density == pytest.approx(math.exp(-1) / 10)
    assert cumulative == pytest.approx(1 - math.exp(-1))


def test_conditional_probability_increases_with_age_for_wear_out_shape() -> None:
    young = conditional_failure_probability(10, 1, shape=2.5, scale_hours=100)
    old = conditional_failure_probability(90, 1, shape=2.5, scale_hours=100)

    assert 0 < young < old < 1


def test_zero_age_has_zero_cumulative_probability() -> None:
    assert weibull_density(0, shape=2, scale_hours=50) == 0
    assert weibull_cdf(0, shape=2, scale_hours=50) == 0


@pytest.mark.parametrize(
    ("shape", "scale"),
    [(0, 10), (-1, 10), (1, 0), (1, -10)],
)
def test_weibull_rejects_invalid_coefficients(shape: float, scale: float) -> None:
    with pytest.raises(ValueError):
        weibull_density(1, shape=shape, scale_hours=scale)


def test_simulator_uses_machine_type_weibull_coefficients() -> None:
    factory = {
        "machine_types": [
            {
                "machine_type": "wearing-machine",
                "name": "Wearing machine",
                "failure_density": {"family": "weibull", "shape": 2, "scale_hours": 0.001},
            }
        ],
        "machines": [
            {
                "machine_id": "machine-01",
                "machine_type": "wearing-machine",
                "metadata": {"processing_time": 10, "repair_time": 5},
            }
        ],
        "process_graph": {
            "nodes": [
                {
                    "node_id": "operation",
                    "kind": "operation",
                    "machine_ids": ["machine-01"],
                }
            ],
            "edges": [],
        },
    }
    scenario = {"seed": 7, "quantity": 1, "routing": ["operation"]}

    result = simulate(factory, scenario)
    breakdown = next(event for event in result.events if event["event_type"] == "breakdown")

    assert breakdown["failure_family"] == "weibull"
    assert breakdown["failure_probability"] == pytest.approx(1)
