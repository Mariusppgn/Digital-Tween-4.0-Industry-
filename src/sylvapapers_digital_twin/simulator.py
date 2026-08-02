"""Readable deterministic event simulation (minutes are the time unit)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from itertools import pairwise
from time import perf_counter
from typing import Any

import networkx as nx

from .graph import build_process_graph, items, mapping, plain
from .reliability import conditional_failure_probability


@dataclass
class MachineState:
    machine_id: str
    processing_time: float
    capacity: int = 1
    buffer_capacity: int = 1
    failure_probability: float = 0.0
    failure_shape: float | None = None
    failure_scale_hours: float | None = None
    repair_time: float = 0.0
    degradation_after: int = 10**9
    degradation_factor: float = 1.0
    defect_rate: float = 0.0
    energy_kw: float = 0.0
    cost_per_hour: float = 0.0
    shared_resource: str | None = None
    shared_capacity: int = 1
    quality_control: bool = False
    duration_cv: float = 0.0
    setup_time: float = 0.0
    maintenance_recovery: float = 0.5
    load_defect_slope: float = 0.0
    last_product_id: str | None = None
    available: list[float] = field(default_factory=list)
    buffers: list[float] = field(default_factory=list)
    counts: list[int] = field(default_factory=list)
    operating_hours: list[float] = field(default_factory=list)

    def initialise(self) -> None:
        self.available = [0.0] * max(1, self.capacity)
        self.buffers = [0.0] * max(1, self.buffer_capacity)
        self.counts = [0] * max(1, self.capacity)
        self.operating_hours = [0.0] * max(1, self.capacity)


@dataclass
class SimulationResult:
    events: list[dict[str, Any]]
    jobs: list[dict[str, Any]]
    graph: nx.DiGraph[str]
    seed: int
    machine_capacities: dict[str, int]
    runtime_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def makespan(self) -> float:
        return max((float(job["completion_time"]) for job in self.jobs), default=0.0)


def _minutes(value: Any, origin: Any, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        end = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
        start = origin if isinstance(origin, datetime) else datetime.fromisoformat(str(origin))
        return max(0.0, (end - start).total_seconds() / 60)
    except (TypeError, ValueError):
        return default


class DigitalTwinSimulator:
    def __init__(self, factory: Any, scenario: Any, product: Any | None = None):
        self.factory = mapping(factory)
        self.scenario = mapping(scenario)
        embedded_products = items(self.scenario.get("products"))
        self.products = {
            str(mapping(value).get("product_id")): mapping(value) for value in embedded_products
        }
        if product is not None:
            supplied = mapping(product)
            self.products[str(supplied.get("product_id") or "default")] = supplied
        self.graph = build_process_graph(factory)
        self.seed = int(self.scenario.get("random_seed") or self.scenario.get("seed") or 42)
        self.random = random.Random(self.seed)
        self.events: list[dict[str, Any]] = []
        self.shared: dict[str, list[float]] = {}
        self.last_load: dict[str, float] = {}
        self.machines = self._machines()

    def _machines(self) -> dict[str, MachineState]:
        result: dict[str, MachineState] = {}
        machine_types = {
            str(mapping(raw).get("machine_type")): mapping(raw)
            for raw in items(self.factory.get("machine_types"))
        }
        configured = {
            str(
                mapping(raw).get("machine_id") or mapping(raw).get("id") or mapping(raw).get("name")
            ): mapping(raw)
            for raw in items(self.factory.get("machines"))
        }
        first_product = next(iter(self.products.values()), {})
        cycle_times = mapping(first_product.get("cycle_time_minutes") or {})
        for identifier, node in self.graph.nodes(data=True):
            selected_ids = [str(value) for value in items(node.get("machine_ids"))]
            if not selected_ids and identifier in configured:
                selected_ids = [identifier]
            selected = [configured[value] for value in selected_ids]
            data = selected[0] if selected else {}
            meta = mapping(data.get("metadata") or {})
            type_config = machine_types.get(str(data.get("machine_type") or ""), {})
            failure_density = mapping(type_config.get("failure_density") or {})
            rate = float(data.get("capacity_per_hour") or meta.get("capacity_per_hour") or 0)
            kind = str(
                node.get("kind")
                or data.get("machine_type")
                or meta.get("machine_type")
                or "process"
            ).lower()
            shared = meta.get("shared_resource") or data.get("shared_resource")
            mtbf_hours = float(data.get("mtbf_hours") or 0)
            processing_time = float(
                cycle_times.get(identifier)
                or meta.get("processing_time")
                or data.get("processing_time")
                or (60 / rate if rate else 10)
            )
            state = MachineState(
                machine_id=identifier,
                processing_time=processing_time,
                capacity=int(
                    meta.get("parallel_stations")
                    or data.get("parallel_stations")
                    or len(selected_ids)
                    or 1
                ),
                buffer_capacity=int(
                    node.get("capacity")
                    or meta.get("buffer_capacity")
                    or data.get("buffer_capacity")
                    or 1
                ),
                failure_probability=float(
                    meta.get("failure_probability")
                    or data.get("failure_probability")
                    or (processing_time / (mtbf_hours * 60) if mtbf_hours else 0)
                ),
                failure_shape=(
                    float(failure_density["shape"]) if failure_density.get("shape") else None
                ),
                failure_scale_hours=(
                    float(failure_density["scale_hours"])
                    if failure_density.get("scale_hours")
                    else None
                ),
                repair_time=float(
                    meta.get("repair_time")
                    or data.get("repair_time")
                    or float(data.get("mttr_hours") or 0) * 60
                ),
                degradation_after=int(
                    meta.get("degradation_after") or data.get("degradation_after") or 10**9
                ),
                degradation_factor=float(
                    meta.get("degradation_factor") or data.get("degradation_factor") or 1
                ),
                defect_rate=float(meta.get("defect_rate") or data.get("defect_rate") or 0),
                energy_kw=float(meta.get("energy_kw") or data.get("energy_kw") or 0),
                cost_per_hour=float(meta.get("cost_per_hour") or data.get("cost_per_hour") or 0),
                shared_resource=str(shared) if shared else None,
                shared_capacity=int(meta.get("shared_resource_capacity") or 1),
                quality_control=bool(
                    meta.get("is_quality_control")
                    or kind in {"qc", "quality", "quality_control", "inspection"}
                ),
                duration_cv=float(meta.get("duration_cv") or 0),
                setup_time=float(meta.get("setup_time") or 0),
                maintenance_recovery=float(meta.get("maintenance_recovery") or 0.5),
                load_defect_slope=float(meta.get("load_defect_slope") or 0),
            )
            state.initialise()
            result[identifier] = state
            if state.shared_resource:
                self.shared.setdefault(state.shared_resource, [0.0] * max(1, state.shared_capacity))
        return result

    def _log(
        self,
        event_type: str,
        time: float,
        job: str,
        machine: str = "",
        duration: float = 0,
        **extra: Any,
    ) -> None:
        self.events.append(
            {
                "event_id": len(self.events) + 1,
                "event_type": event_type,
                "time": round(time, 6),
                "duration": round(duration, 6),
                "job_id": job,
                "machine_id": machine,
                **extra,
            }
        )

    def _route(self, product: dict[str, Any] | None = None) -> list[str]:
        configured = (product or {}).get("routing") or self.scenario.get("routing")
        if configured:
            route = []
            for raw in items(configured):
                value = plain(raw)
                if isinstance(value, dict):
                    value = value.get("machine_id") or value.get("node_id") or value.get("id")
                route.append(str(value))
            unknown = [node for node in route if node not in self.graph]
            if unknown:
                raise ValueError(f"Product routing references unknown process nodes: {unknown}")
            disconnected = [
                (source, target)
                for source, target in pairwise(route)
                if not self.graph.has_edge(source, target)
            ]
            if disconnected:
                raise ValueError(f"Product routing contains disconnected steps: {disconnected}")
            return route
        return self._route_from_graph(product or {})

    def _route_from_graph(self, product: dict[str, Any]) -> list[str]:
        """Derive one deterministic product route from editable graph conditions."""
        sources = [
            node for node, data in self.graph.nodes(data=True) if data.get("kind") == "source"
        ]
        if not sources:
            sources = [node for node, degree in self.graph.in_degree() if degree == 0]
        if not sources:
            raise ValueError("The process graph requires at least one source")
        metadata = mapping(product.get("metadata") or {})
        tags = {
            str(value)
            for value in (
                product.get("product_id"),
                metadata.get("route_condition"),
                metadata.get("grade"),
            )
            if value
        }
        current = sorted(sources)[0]
        route: list[str] = (
            [current] if self.graph.nodes[current].get("kind") not in {"source", "sink"} else []
        )
        visited: set[tuple[str, str]] = set()
        while (
            self.graph.nodes[current].get("kind") != "sink"
            and self.graph.out_degree(current) > 0
        ):
            candidates = [
                (current, target, data)
                for _, target, data in self.graph.out_edges(current, data=True)
                if (current, target) not in visited
            ]
            if not candidates:
                raise ValueError(f"No terminating product route from process node {current!r}")
            matching = [edge for edge in candidates if str(edge[2].get("condition")) in tags]
            unconditional = [edge for edge in candidates if not edge[2].get("condition")]
            choices = matching or unconditional or candidates
            # When only outcome probabilities distinguish branches, follow the
            # nominal (highest-probability) path; stochastic QC is handled by
            # the machine event model and losses are recorded separately.
            selected = sorted(
                choices,
                key=lambda edge: (-float(edge[2].get("probability") or 0), str(edge[1])),
            )[0]
            visited.add((selected[0], selected[1]))
            current = selected[1]
            if self.graph.nodes[current].get("kind") not in {"source", "sink"}:
                route.append(current)
            if len(visited) > self.graph.number_of_edges():
                raise ValueError("Process route did not terminate")
        return route

    def _orders(self) -> list[dict[str, Any]]:
        origin = self.scenario.get("start_at") or self.scenario.get("start_time")
        raw_orders = items(self.scenario.get("orders")) or [
            {
                "order_id": "ORDER-001",
                "quantity": self.scenario.get("quantity") or self.scenario.get("demand") or 5,
                "due_date": self.scenario.get("due_time") or 240,
            }
        ]
        default_due = _minutes(
            self.scenario.get("end_at") or self.scenario.get("end_time"), origin, 240
        )
        interval = float(self.scenario.get("interarrival_time") or 0)
        jobs, sequence = [], 0
        for raw in raw_orders:
            order = mapping(raw)
            for unit in range(1, int(order.get("quantity") or 1) + 1):
                jobs.append(
                    {
                        "job_id": f"{order.get('order_id', 'ORDER')}-{unit:04d}",
                        "order_id": str(order.get("order_id") or "ORDER"),
                        "product_id": str(order.get("product_id") or ""),
                        "release_time": _minutes(
                            order.get("release_at") or order.get("release_date"), origin, 0
                        )
                        + sequence * interval,
                        "due_time": _minutes(
                            order.get("due_at") or order.get("due_date"), origin, default_due
                        ),
                    }
                )
                sequence += 1
        return jobs

    def _process(
        self,
        state: MachineState,
        arrival: float,
        job: str,
        product_id: str,
        processing_time: float | None = None,
    ) -> float:
        buffer_index = min(range(len(state.buffers)), key=state.buffers.__getitem__)
        entered = max(arrival, state.buffers[buffer_index])
        shared = self.shared.get(state.shared_resource or "")
        choices: list[tuple[float, int, int | None]] = []
        for machine_index, free in enumerate(state.available):
            if shared is None:
                choices.append((max(entered, free), machine_index, None))
            else:
                choices.extend(
                    (max(entered, free, shared_free), machine_index, shared_index)
                    for shared_index, shared_free in enumerate(shared)
                )
        start, machine_index, shared_index = min(choices)
        wait = max(0.0, start - arrival)
        if start > arrival:
            self._log(
                "buffer_wait",
                arrival,
                job,
                state.machine_id,
                start - arrival,
                buffer_capacity=state.buffer_capacity,
            )
        state.buffers[buffer_index] = start
        if (
            state.last_product_id is not None
            and state.last_product_id != product_id
            and state.setup_time > 0
        ):
            self._log(
                "setup",
                start,
                job,
                state.machine_id,
                state.setup_time,
                previous_product_id=state.last_product_id,
                product_id=product_id,
            )
            start += state.setup_time
        degraded = state.counts[machine_index] >= state.degradation_after
        nominal = processing_time if processing_time is not None else state.processing_time
        stochastic_factor = self.random.uniform(
            max(0.5, 1 - state.duration_cv),
            1 + state.duration_cv,
        )
        duration = nominal * stochastic_factor * (state.degradation_factor if degraded else 1)
        if degraded:
            self._log("degradation", start, job, state.machine_id)
        failure_probability = state.failure_probability
        if state.failure_shape is not None and state.failure_scale_hours is not None:
            failure_probability = conditional_failure_probability(
                state.operating_hours[machine_index],
                duration / 60,
                shape=state.failure_shape,
                scale_hours=state.failure_scale_hours,
            )
        if self.random.random() < failure_probability:
            self._log(
                "breakdown",
                start,
                job,
                state.machine_id,
                state.repair_time,
                cost=round(state.repair_time * state.cost_per_hour / 60, 6),
                failure_probability=round(failure_probability, 9),
                operating_age_hours=round(state.operating_hours[machine_index], 6),
                failure_family=("weibull" if state.failure_shape is not None else "legacy"),
            )
            start += state.repair_time
            state.counts[machine_index] = max(
                0,
                int(state.counts[machine_index] * (1 - state.maintenance_recovery)),
            )
            state.operating_hours[machine_index] *= 1 - state.maintenance_recovery
            self._log("repair", start, job, state.machine_id)
            self._log(
                "maintenance_complete",
                start,
                job,
                state.machine_id,
                degradation_cycles=state.counts[machine_index],
            )
        end = start + duration
        load = min(1.0, wait / max(nominal, 1e-9))
        self._log(
            "operation_start",
            start,
            job,
            state.machine_id,
            shared_resource=state.shared_resource or "",
        )
        self._log(
            "operation_end",
            end,
            job,
            state.machine_id,
            duration,
            started_at=round(start, 6),
            energy=round(
                state.energy_kw * duration / 60 * (1 + 0.1 * load + (0.1 if degraded else 0)),
                6,
            ),
            cost=round(state.cost_per_hour * duration / 60, 6),
            degraded=degraded,
        )
        state.available[machine_index] = end
        state.counts[machine_index] += 1
        state.operating_hours[machine_index] += duration / 60
        state.last_product_id = product_id
        self.last_load[state.machine_id] = load
        if shared is not None and shared_index is not None:
            shared[shared_index] = end
        return end

    def run(self) -> SimulationResult:
        started = perf_counter()
        jobs = []
        for job in self._orders():
            product = self.products.get(job["product_id"], next(iter(self.products.values()), {}))
            route = self._route(product)
            if not route:
                raise ValueError("At least one process operation is required")
            cycle_times = mapping(product.get("cycle_time_minutes") or {})
            now, index, first_pass, lost = (
                float(job["release_time"]),
                0,
                True,
                False,
            )
            self._log("order_released", now, job["job_id"])
            while index < len(route):
                state = self.machines[route[index]]
                duration = cycle_times.get(route[index])
                now = self._process(
                    state,
                    now,
                    job["job_id"],
                    job["product_id"],
                    float(duration) if duration is not None else None,
                )
                if state.quality_control:
                    defect_probability = min(
                        1.0,
                        state.defect_rate
                        + state.load_defect_slope * self.last_load.get(state.machine_id, 0.0),
                    )
                    failed = self.random.random() < defect_probability
                    self._log(
                        "qc_fail" if failed else "qc_pass", now, job["job_id"], state.machine_id
                    )
                    if failed:
                        first_pass = False
                        lost = True
                        self._log(
                            "material_loss",
                            now,
                            job["job_id"],
                            state.machine_id,
                            quantity=1,
                            quantity_unit=str(product.get("unit") or "unit"),
                            reason="quality_nonconformity",
                        )
                        break
                index += 1
            delay = max(0.0, now - float(job["due_time"]))
            self._log(
                "completed",
                now,
                job["job_id"],
                due_time=job["due_time"],
                delay=round(delay, 6),
                accepted=not lost,
            )
            jobs.append(
                {
                    **job,
                    "completion_time": round(now, 6),
                    "cycle_time": round(now - float(job["release_time"]), 6),
                    "delay": round(delay, 6),
                    "on_time": delay == 0,
                    "first_pass": first_pass,
                    "accepted": not lost,
                    "material_loss": 1 if lost else 0,
                }
            )
        self.events.sort(key=lambda event: (event["time"], event["event_id"]))
        for number, event in enumerate(self.events, 1):
            event["event_id"] = number
        return SimulationResult(
            events=self.events,
            jobs=jobs,
            graph=self.graph,
            seed=self.seed,
            machine_capacities={key: value.capacity for key, value in self.machines.items()},
            runtime_seconds=round(perf_counter() - started, 6),
            metadata={
                "factory_id": self.factory.get("factory_id", "unknown"),
                "scenario_id": self.scenario.get("scenario_id", "unknown"),
                "schema_version": self.scenario.get("schema_version", "1.0.0"),
                "code_version": "0.2.0",
            },
        )


def simulate(factory: Any, scenario: Any, product: Any | None = None) -> SimulationResult:
    return DigitalTwinSimulator(factory, scenario, product).run()
