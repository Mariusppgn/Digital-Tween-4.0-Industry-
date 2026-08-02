from sylvapapers_digital_twin import build_process_graph, simulate


def factory_config():
    machines = [
        {
            "machine_id": "cut",
            "name": "Découpe",
            "machine_type": "process",
            "metadata": {"processing_time": 4, "energy_kw": 3, "cost_per_hour": 30},
        },
        {
            "machine_id": "forming",
            "name": "Formation de feuille",
            "machine_type": "process",
            "metadata": {
                "processing_time": 10,
                "parallel_stations": 2,
                "buffer_capacity": 1,
                "degradation_after": 1,
                "degradation_factor": 1.2,
            },
        },
        {
            "machine_id": "cure",
            "name": "Cuisson",
            "machine_type": "process",
            "metadata": {
                "processing_time": 8,
                "shared_resource": "oven",
                "shared_resource_capacity": 1,
                "failure_probability": 1,
                "repair_time": 2,
                "energy_kw": 12,
                "cost_per_hour": 90,
            },
        },
        {
            "machine_id": "qc",
            "name": "Contrôle",
            "machine_type": "quality_control",
            "metadata": {"processing_time": 2, "defect_rate": 1},
        },
    ]
    return {
        "factory_id": "SYLVAPAPERS",
        "machines": machines,
        "process_graph": {
            "nodes": [machine["machine_id"] for machine in machines],
            "edges": [["cut", "forming"], ["forming", "cure"], ["cure", "qc"]],
        },
    }


def scenario_config():
    return {
        "scenario_id": "baseline",
        "random_seed": 7,
        "orders": [{"order_id": "PO-1", "product_id": "paper-roll", "quantity": 3, "due_at": 200}],
    }


def test_graph_and_deterministic_simulation_cover_initial_behaviours():
    graph = build_process_graph(factory_config())
    assert list(graph.nodes) == ["cut", "forming", "cure", "qc"]
    assert graph.has_edge("forming", "cure")

    first = simulate(factory_config(), scenario_config())
    second = simulate(factory_config(), scenario_config())
    assert first.events == second.events
    assert first.jobs == second.jobs
    assert first.machine_capacities["forming"] == 2
    assert len(first.jobs) == 3
    event_types = {event["event_type"] for event in first.events}
    assert {
        "buffer_wait",
        "breakdown",
        "repair",
        "degradation",
        "qc_fail",
        "material_loss",
        "completed",
    } <= event_types
    assert all(job["material_loss"] == 1 for job in first.jobs)


def test_quality_rejection_is_recorded_as_material_loss():
    result = simulate(factory_config(), scenario_config())

    assert all(not job["accepted"] for job in result.jobs)
    assert all(job["material_loss"] == 1 for job in result.jobs)
    assert sum(event["event_type"] == "material_loss" for event in result.events) == 3


def test_limited_shared_resource_serialises_cure_operations():
    result = simulate(factory_config(), scenario_config())
    starts = [
        event["time"]
        for event in result.events
        if event["event_type"] == "operation_start" and event["machine_id"] == "cure"
    ]
    ends = [
        event["time"]
        for event in result.events
        if event["event_type"] == "operation_end" and event["machine_id"] == "cure"
    ]
    assert all(next_start >= end for next_start, end in zip(starts[1:], ends, strict=False))
