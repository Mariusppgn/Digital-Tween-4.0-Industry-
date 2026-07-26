from pathlib import Path

from asteria_contracts import load_factory_config, load_simulation_scenario

ROOT = Path(__file__).resolve().parents[1]


def test_reference_factory_has_branch_parallel_buffer_qc_and_rework() -> None:
    factory = load_factory_config(ROOT / "configs" / "factory.yaml")
    nodes = {node.node_id: node for node in factory.process_graph.nodes}
    edges = {(edge.source, edge.target, edge.condition) for edge in factory.process_graph.edges}

    assert len(factory.machines) >= 7
    assert len(nodes["layup"].machine_ids) == 2
    assert nodes["intermediate-buffer"].kind == "buffer"
    assert nodes["autoclave"].machine_ids == ["autoclave-01"]
    assert nodes["finishing"].machine_ids == ["finish-01"]
    assert nodes["qc"].kind == "quality_control"
    assert nodes["rework"].kind == "rework"
    assert ("qc", "sink", "pass") in edges
    assert ("qc", "rework", "fail") in edges
    assert ("rework", "finishing", None) in edges
    assert {calendar.resource_id for calendar in factory.resource_calendars} == {
        "operator-team",
        "maintenance-technician",
    }


def test_reference_scenario_has_two_products_and_valid_orders() -> None:
    scenario = load_simulation_scenario(ROOT / "data" / "examples" / "simulation_scenario.json")
    assert {product.product_id for product in scenario.products} == {"panel-a", "panel-b"}
    assert len(scenario.orders) == 2
    assert all(order.quantity > 0 for order in scenario.orders)
