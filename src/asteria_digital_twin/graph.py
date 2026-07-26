"""NetworkX process-graph adapter for ``asteria_contracts`` models."""

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

    Cycles are accepted because the reference factory contains a bounded quality
    rework loop. Product routings prevent the simulator from following that loop
    indefinitely.
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
            if isinstance(edge, Mapping):
                source = edge.get("source") or edge.get("from_node") or edge.get("from")
                target = edge.get("target") or edge.get("to_node") or edge.get("to")
            else:
                source, target = list(edge)[:2]
            if source is None or target is None:
                raise ValueError(f"Invalid process edge: {edge!r}")
            graph.add_edge(str(source), str(target))
    if graph.number_of_edges() == 0:
        identifiers = [node_id(machine) for machine in machines]
        graph.add_edges_from(pairwise(identifiers))
    known = {node_id(machine) for machine in machines}
    referenced = {
        str(machine_id)
        for _, attributes in graph.nodes(data=True)
        for machine_id in items(attributes.get("machine_ids"))
    }
    if missing := referenced - known:
        raise ValueError(f"Graph references unknown machines: {sorted(missing)}")
    return graph
