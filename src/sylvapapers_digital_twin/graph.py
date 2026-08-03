"""NetworkX process-graph adapter for ``sylvapapers_contracts`` models."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import pairwise
from typing import Any

import networkx as nx


def plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="python")
    if hasattr(value, "dict"):
        return value.dict()
    return value


def mapping(value: Any) -> dict[str, Any]:
    value = plain(value)
    if not isinstance(value, Mapping):
        raise TypeError(f"Expected a mapping or Pydantic model, got {type(value).__name__}")
    return dict(value)


def items(value: Any) -> list[Any]:
    value = plain(value)
    if value is None:
        return []
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return [value]


def node_id(value: Any) -> str:
    if isinstance(plain(value), str):
        return str(value)
    data = mapping(value)
    identifier = data.get("machine_id") or data.get("node_id") or data.get("id") or data.get("name")
    if not identifier:
        raise ValueError(f"Process node has no identifier: {data!r}")
    return str(identifier)


def build_process_graph(factory: Any) -> nx.DiGraph[str]:
    """Build a validated directed process graph from a contract or mapping.

    Nominal flow edges must remain acyclic. One separately labelled recycling
    edge may close a feedback loop; its execution is bounded by the explicit
    graph-level recycling configuration rather than traversed by route search.
    """
    config = mapping(factory)
    machines = items(config.get("machines"))
    graph_config = plain(config.get("process_graph") or {})
    graph: nx.DiGraph[str] = nx.DiGraph()
    configured_nodes = items(graph_config.get("nodes")) if isinstance(graph_config, Mapping) else []
    if configured_nodes:
        for raw in configured_nodes:
            data = plain(raw)
            graph.add_node(node_id(raw), **({} if isinstance(data, str) else mapping(raw)))
    else:
        for raw in machines:
            graph.add_node(node_id(raw), **mapping(raw))
    if isinstance(graph_config, Mapping):
        for raw in items(graph_config.get("edges")):
            edge = plain(raw)
            attributes: dict[str, Any] = {}
            if isinstance(edge, Mapping):
                source = edge.get("source") or edge.get("from_node") or edge.get("from")
                target = edge.get("target") or edge.get("to_node") or edge.get("to")
                attributes = {
                    str(key): plain(value)
                    for key, value in edge.items()
                    if key not in {"source", "target", "from_node", "to_node", "from", "to"}
                }
            else:
                source, target = list(edge)[:2]
            if source is None or target is None:
                raise ValueError(f"Invalid process edge: {edge!r}")
            graph.add_edge(str(source), str(target), **attributes)
    if graph.number_of_edges() == 0:
        identifiers = [node_id(machine) for machine in machines]
        graph.add_edges_from(pairwise(identifiers))
    configured_node_ids = (
        {node_id(raw) for raw in configured_nodes} if configured_nodes else set(graph.nodes)
    )
    edge_node_ids = {str(source) for source, _ in graph.edges} | {
        str(target) for _, target in graph.edges
    }
    if dangling := edge_node_ids - configured_node_ids:
        raise ValueError(f"Process edges reference unknown nodes: {sorted(dangling)}")
    known = {node_id(machine) for machine in machines}
    referenced = {
        str(machine_id)
        for _, attributes in graph.nodes(data=True)
        for machine_id in items(attributes.get("machine_ids"))
    }
    if missing := referenced - known:
        raise ValueError(f"Graph references unknown machines: {sorted(missing)}")
    recycling = mapping(graph_config.get("recycling")) if graph_config.get("recycling") else None
    recycle_edges = [
        (source, target)
        for source, target, attributes in graph.edges(data=True)
        if attributes.get("relation", "forward") == "recycle"
    ]
    if len(recycle_edges) > 1:
        raise ValueError("Only one controlled recycling edge is supported")
    if recycle_edges and recycling is None:
        raise ValueError("A recycle edge requires an explicit recycling configuration")
    if recycling is not None:
        expected = (
            str(recycling.get("source_node_id")),
            str(recycling.get("return_to_node_id")),
        )
        if recycle_edges != [expected]:
            raise ValueError("Recycle edge endpoints must match the recycling configuration")
        if not 0 <= float(recycling.get("recovery_yield", 0.75)) <= 1:
            raise ValueError("Recycling recovery_yield must be between zero and one")
        if not 1 <= int(recycling.get("max_loops", 1)) <= 20:
            raise ValueError("Recycling max_loops must be between one and twenty")
        if graph.nodes[expected[0]].get("kind") != "quality_control":
            raise ValueError("Recycling must originate from a quality-control node")
        if graph.nodes[expected[1]].get("kind") != "operation":
            raise ValueError("Recycling must return to an operation node")
        graph.graph["recycling"] = recycling
    nominal_graph = nx.DiGraph(
        (source, target)
        for source, target, attributes in graph.edges(data=True)
        if attributes.get("relation", "forward") == "forward"
    )
    nominal_graph.add_nodes_from(graph.nodes)
    if not nx.is_directed_acyclic_graph(nominal_graph):
        raise ValueError("Forward process edges must form an acyclic graph")
    if recycling is not None and not nx.has_path(
        nominal_graph,
        str(recycling["return_to_node_id"]),
        str(recycling["source_node_id"]),
    ):
        raise ValueError("Recycle edge must return to an upstream operation")
    return graph
