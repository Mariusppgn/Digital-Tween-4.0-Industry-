from pathlib import Path

from sylvapapers_contracts import load_factory_config, load_simulation_scenario

ROOT = Path(__file__).resolve().parents[1]


def test_reference_factory_models_paper_mill_series_parallel_flow() -> None:
    factory = load_factory_config(ROOT / "configs" / "factory.yaml")
    nodes = {node.node_id: node for node in factory.process_graph.nodes}
    edges = {(edge.source, edge.target, edge.condition) for edge in factory.process_graph.edges}

    assert factory.factory_id == "sylvapapers-demo"
    assert len(factory.machines) >= 15
    assert len(nodes["debarking"].machine_ids) == 2
    assert len(nodes["drying"].machine_ids) == 2
    assert nodes["chips-buffer"].kind == "buffer"
    assert nodes["quality-control"].kind == "quality_control"
    assert ("chips-buffer", "kraft-pulping", "papier_kraft") in edges
    assert ("chips-buffer", "tmp-pulping", "papier_impression") in edges
    assert ("chips-buffer", "board-pulping", "carton") in edges
    assert ("kraft-pulping", "pulp-washing", None) in edges
    assert ("tmp-pulping", "pulp-washing", None) in edges
    assert ("quality-control", "paper-rolls", "conforme") in edges
    assert ("quality-control", "measured-losses", "non_conforme") in edges
    assert nodes["measured-losses"].metadata["kpi"] == "quality_loss_rate"
    assert "rework" not in nodes
    assert all(node.position is not None for node in nodes.values())
    assert {calendar.resource_id for calendar in factory.resource_calendars} == {
        "production-team",
        "maintenance-team",
    }


def test_reference_factory_defines_one_weibull_density_per_machine_type() -> None:
    factory = load_factory_config(ROOT / "configs" / "factory.yaml")
    machine_types = {definition.machine_type: definition for definition in factory.machine_types}

    assert {machine.machine_type for machine in factory.machines} == set(machine_types)
    assert {definition.failure_density.family for definition in machine_types.values()} == {
        "weibull"
    }
    assert all(
        definition.metadata["calibration_status"] == "synthetic_hypothesis"
        for definition in machine_types.values()
    )


def test_reference_scenario_has_three_configurable_paper_products() -> None:
    scenario = load_simulation_scenario(ROOT / "data" / "examples" / "simulation_scenario.json")
    assert {product.product_id for product in scenario.products} == {
        "kraft-paper-roll",
        "linerboard-roll",
        "printing-paper-roll",
    }
    assert len(scenario.orders) == 2
    assert all(product.unit == "roll" for product in scenario.products)
    assert all(order.quantity > 0 for order in scenario.orders)
    enabled = {product.product_id: product.enabled for product in scenario.products}
    assert enabled == {
        "kraft-paper-roll": True,
        "linerboard-roll": False,
        "printing-paper-roll": True,
    }
    assert {product.metadata["route_condition"] for product in scenario.products} == {
        "carton",
        "papier_impression",
        "papier_kraft",
    }
