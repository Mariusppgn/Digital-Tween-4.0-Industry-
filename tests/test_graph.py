from asteria_digital_twin import DigitalTwinSimulator, build_process_graph


def test_graph_preserves_material_flow_attributes() -> None:
    graph = build_process_graph(
        {
            "machines": [
                {"machine_id": "a"},
                {"machine_id": "b"},
            ],
            "process_graph": {
                "nodes": [
                    {"node_id": "a", "kind": "operation"},
                    {"node_id": "b", "kind": "operation"},
                ],
                "edges": [
                    {
                        "source": "a",
                        "target": "b",
                        "condition": "kraft",
                        "probability": 0.7,
                    }
                ],
            },
        }
    )

    assert graph.edges["a", "b"]["condition"] == "kraft"
    assert graph.edges["a", "b"]["probability"] == 0.7


def test_product_route_is_derived_from_edge_condition_when_not_explicit() -> None:
    factory = {
        "machines": [
            {"machine_id": "common-machine", "machine_type": "process"},
            {"machine_id": "kraft-machine", "machine_type": "process"},
            {"machine_id": "print-machine", "machine_type": "process"},
        ],
        "process_graph": {
            "nodes": [
                {"node_id": "source", "kind": "source"},
                {
                    "node_id": "common",
                    "kind": "operation",
                    "machine_ids": ["common-machine"],
                },
                {
                    "node_id": "kraft",
                    "kind": "operation",
                    "machine_ids": ["kraft-machine"],
                },
                {
                    "node_id": "print",
                    "kind": "operation",
                    "machine_ids": ["print-machine"],
                },
                {"node_id": "sink", "kind": "sink"},
            ],
            "edges": [
                {"source": "source", "target": "common"},
                {"source": "common", "target": "kraft", "condition": "kraft"},
                {"source": "common", "target": "print", "condition": "print"},
                {"source": "kraft", "target": "sink"},
                {"source": "print", "target": "sink"},
            ],
        },
    }
    scenario = {"products": []}
    simulator = DigitalTwinSimulator(factory, scenario)

    assert simulator._route({"metadata": {"route_condition": "kraft"}}) == [
        "common",
        "kraft",
    ]
    assert simulator._route({"metadata": {"route_condition": "print"}}) == [
        "common",
        "print",
    ]
