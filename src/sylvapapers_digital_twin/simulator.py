"""Readable deterministic event simulation (minutes are the time unit)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
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
    instance_ids: list[str] = field(default_factory=list)
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
    preventive_interval_hours: float | None = None
    preventive_on_degradation: bool = False
    preventive_duration: float = 0.0
    preventive_recovery: float = 1.0
    emission_factor_kg_co2e_per_kwh: float = 0.05
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
        if not self.instance_ids:
            self.instance_ids = [
                self.machine_id if self.capacity == 1 else f"{self.machine_id}-{index + 1:02d}"
                for index in range(self.capacity)
            ]
        elif len(self.instance_ids) < self.capacity:
            self.instance_ids.extend(
                f"{self.machine_id}-{index + 1:02d}"
                for index in range(len(self.instance_ids), self.capacity)
            )


@dataclass
class SimulationResult:
    events: list[dict[str, Any]]
    jobs: list[dict[str, Any]]
    graph: nx.DiGraph[str]
    seed: int
    machine_capacities: dict[str, int]
    runtime_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    machine_states: list[dict[str, Any]] = field(default_factory=list)
    sensor_records: list[dict[str, Any]] = field(default_factory=list)
    failure_events: list[dict[str, Any]] = field(default_factory=list)
    maintenance_interventions: list[dict[str, Any]] = field(default_factory=list)
    queue_history: list[dict[str, Any]] = field(default_factory=list)
    work_in_progress: list[dict[str, Any]] = field(default_factory=list)
    recycling_records: list[dict[str, Any]] = field(default_factory=list)
    final_state: dict[str, Any] = field(default_factory=dict)

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


def _first_configured(*values: Any, default: Any) -> Any:
    """Return the first explicit value while preserving valid zeroes and false values."""
    return next((value for value in values if value is not None), default)


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
        # Synthetic sensors must not alter the process-event random stream.
        self.sensor_random = random.Random(self.seed ^ 0x5EED5EED)
        self.events: list[dict[str, Any]] = []
        self.machine_states: list[dict[str, Any]] = []
        self.sensor_records: list[dict[str, Any]] = []
        self.failure_events: list[dict[str, Any]] = []
        self.maintenance_interventions: list[dict[str, Any]] = []
        self.queue_history: list[dict[str, Any]] = []
        self.work_in_progress: list[dict[str, Any]] = []
        self.recycling_records: list[dict[str, Any]] = []
        self.current_wip = 0
        self.shared: dict[str, list[float]] = {}
        self.last_load: dict[str, float] = {}
        self.machines = self._machines()
        self.recycling = (
            mapping(self.graph.graph["recycling"])
            if self.graph.graph.get("recycling") is not None
            else None
        )

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
            type_meta = mapping(type_config.get("metadata") or {})
            raw_preventive_interval = _first_configured(
                meta.get("preventive_interval_hours"),
                data.get("preventive_interval_hours"),
                type_meta.get("preventive_interval_hours"),
                default=None,
            )
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
                instance_ids=selected_ids,
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
                maintenance_recovery=float(
                    _first_configured(meta.get("maintenance_recovery"), default=0.5)
                ),
                load_defect_slope=float(meta.get("load_defect_slope") or 0),
                preventive_interval_hours=(
                    float(raw_preventive_interval) if raw_preventive_interval is not None else None
                ),
                preventive_on_degradation=bool(
                    _first_configured(
                        meta.get("preventive_on_degradation"),
                        data.get("preventive_on_degradation"),
                        type_meta.get("preventive_on_degradation"),
                        default=False,
                    )
                ),
                preventive_duration=float(
                    _first_configured(
                        meta.get("preventive_maintenance_duration_minutes"),
                        data.get("preventive_maintenance_duration_minutes"),
                        type_meta.get("preventive_maintenance_duration_minutes"),
                        default=60,
                    )
                ),
                preventive_recovery=float(
                    _first_configured(
                        meta.get("preventive_maintenance_recovery"),
                        data.get("preventive_maintenance_recovery"),
                        type_meta.get("preventive_maintenance_recovery"),
                        default=1,
                    )
                ),
                emission_factor_kg_co2e_per_kwh=float(
                    _first_configured(
                        meta.get("emission_factor_kg_co2e_per_kwh"),
                        data.get("emission_factor_kg_co2e_per_kwh"),
                        type_meta.get("emission_factor_kg_co2e_per_kwh"),
                        default=0.05,
                    )
                ),
            )
            if state.preventive_interval_hours is not None and state.preventive_interval_hours <= 0:
                raise ValueError("preventive_interval_hours must be strictly positive")
            if state.preventive_duration < 0:
                raise ValueError("preventive maintenance duration must be non-negative")
            if not 0 <= state.maintenance_recovery <= 1:
                raise ValueError("maintenance_recovery must be between zero and one")
            if not 0 <= state.preventive_recovery <= 1:
                raise ValueError("preventive_maintenance_recovery must be between zero and one")
            if state.emission_factor_kg_co2e_per_kwh < 0:
                raise ValueError("emission factor must be non-negative")
            state.initialise()
            result[identifier] = state
            if state.shared_resource:
                self.shared.setdefault(state.shared_resource, [0.0] * max(1, state.shared_capacity))
        return result

    def _timestamp(self, minute: float) -> str:
        """Map simulation minutes to an ISO timestamp for public A-to-B records."""
        raw_origin = self.scenario.get("start_at") or self.scenario.get("start_time")
        try:
            origin = (
                raw_origin
                if isinstance(raw_origin, datetime)
                else datetime.fromisoformat(str(raw_origin))
            )
        except (TypeError, ValueError):
            origin = datetime(2000, 1, 1, tzinfo=UTC)
        if origin.tzinfo is None:
            origin = origin.replace(tzinfo=UTC)
        return (origin + timedelta(minutes=minute)).isoformat()

    def _machine_state(
        self,
        state: MachineState,
        instance_index: int,
        time: float,
        status: str,
        job: str = "",
        remaining_minutes: float = 0.0,
    ) -> None:
        self.machine_states.append(
            {
                "machine_id": state.instance_ids[instance_index],
                "process_node_id": state.machine_id,
                "instance_index": instance_index,
                "time_minutes": round(time, 6),
                "timestamp": self._timestamp(time),
                "status": status,
                "job_id": job,
                "operating_age_hours": round(state.operating_hours[instance_index], 6),
                "remaining_minutes": round(max(0.0, remaining_minutes), 6),
                "utilisation": 1.0 if status == "running" else 0.0,
            }
        )

    def _sensor_record(
        self,
        state: MachineState,
        instance_index: int,
        time: float,
        job: str,
        *,
        load: float,
        degraded: bool,
        failure_probability: float,
    ) -> None:
        """Emit one deterministic, explicitly synthetic sensor snapshot per operation."""
        age = state.operating_hours[instance_index]
        if state.failure_scale_hours:
            degradation_index = min(2.0, age / state.failure_scale_hours)
        else:
            degradation_index = min(2.0, state.counts[instance_index] / 1000)
        stress = load + degradation_index + (0.2 if degraded else 0.0)
        noise = self.sensor_random.uniform(-0.03, 0.03)
        power = state.energy_kw * (0.65 + 0.35 * max(0.0, min(1.0, load)))
        self.sensor_records.append(
            {
                "sensor_id": f"synthetic-{state.instance_ids[instance_index]}",
                "machine_id": state.instance_ids[instance_index],
                "process_node_id": state.machine_id,
                "time_minutes": round(time, 6),
                "timestamp": self._timestamp(time),
                "job_id": job,
                "quality": "uncertain" if degraded else "good",
                "load_ratio": round(max(0.0, min(1.0, load)), 6),
                "temperature_c": round(35 + 42 * stress + 8 * noise, 6),
                "vibration_mm_s": round(max(0.0, 1.2 + 4.5 * stress + noise), 6),
                "pressure_bar": round(max(0.0, 2.0 + 3.0 * load + 0.5 * noise), 6),
                "power_kw": round(max(0.0, power * (1 + noise)), 6),
                "operating_age_hours": round(age, 6),
                "degradation_index": round(degradation_index, 6),
                "failure_probability": round(failure_probability, 9),
                "synthetic": True,
            }
        )

    def _wip(
        self,
        time: float,
        job: str,
        product_id: str,
        process_node_id: str,
        status: str,
        delta: int = 0,
    ) -> None:
        self.current_wip += delta
        self.work_in_progress.append(
            {
                "time_minutes": round(time, 6),
                "timestamp": self._timestamp(time),
                "job_id": job,
                "product_id": product_id,
                "process_node_id": process_node_id,
                "status": status,
                "wip_delta": delta,
                "total_wip": self.current_wip,
            }
        )

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
                or self.graph.edges[source, target].get("relation", "forward") != "forward"
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
            forward_indegree = {
                node: sum(
                    attributes.get("relation", "forward") == "forward"
                    for _, _, attributes in self.graph.in_edges(node, data=True)
                )
                for node in self.graph
            }
            sources = [node for node, degree in forward_indegree.items() if degree == 0]
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
            self.graph.nodes[current].get("kind") != "sink" and self.graph.out_degree(current) > 0
        ):
            candidates = [
                (current, target, data)
                for _, target, data in self.graph.out_edges(current, data=True)
                if data.get("relation", "forward") == "forward"
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
        queued_jobs = sum(buffer_release > arrival for buffer_release in state.buffers)
        self.queue_history.append(
            {
                "machine_id": state.machine_id,
                "time_minutes": round(arrival, 6),
                "timestamp": self._timestamp(arrival),
                "job_id": job,
                "arrival_minutes": round(arrival, 6),
                "service_start_minutes": round(start, 6),
                "wait_minutes": round(wait, 6),
                "queue_length": queued_jobs,
                "buffer_capacity": state.buffer_capacity,
                "buffer_index": buffer_index,
            }
        )
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
            self._machine_state(
                state,
                machine_index,
                start,
                "setup",
                job,
                state.setup_time,
            )
            start += state.setup_time
        nominal = processing_time if processing_time is not None else state.processing_time
        stochastic_factor = self.random.uniform(
            max(0.5, 1 - state.duration_cv),
            1 + state.duration_cv,
        )
        projected_duration = nominal * stochastic_factor
        interval = state.preventive_interval_hours
        if (
            interval is not None
            and state.operating_hours[machine_index] + projected_duration / 60 >= interval
        ) or (
            state.preventive_on_degradation
            and state.counts[machine_index] >= state.degradation_after
        ):
            maintenance_start = start
            age_before = state.operating_hours[machine_index]
            self._log(
                "preventive_maintenance_start",
                maintenance_start,
                job,
                state.machine_id,
                state.preventive_duration,
                machine_instance_id=state.instance_ids[machine_index],
                operating_age_hours=round(age_before, 6),
                threshold_hours=round(interval, 6) if interval is not None else "",
            )
            self._machine_state(
                state,
                machine_index,
                maintenance_start,
                "maintenance",
                job,
                state.preventive_duration,
            )
            start += state.preventive_duration
            state.operating_hours[machine_index] *= 1 - state.preventive_recovery
            state.counts[machine_index] = max(
                0,
                int(state.counts[machine_index] * (1 - state.preventive_recovery)),
            )
            self._log(
                "preventive_maintenance_complete",
                start,
                job,
                state.machine_id,
                machine_instance_id=state.instance_ids[machine_index],
                operating_age_hours=round(state.operating_hours[machine_index], 6),
            )
            self.maintenance_interventions.append(
                {
                    "intervention_id": f"PM-{len(self.maintenance_interventions) + 1:06d}",
                    "machine_id": state.instance_ids[machine_index],
                    "process_node_id": state.machine_id,
                    "time_minutes": round(maintenance_start, 6),
                    "timestamp": self._timestamp(maintenance_start),
                    "completed_at_minutes": round(start, 6),
                    "completed_at": self._timestamp(start),
                    "job_id": job,
                    "maintenance_type": "preventive",
                    "duration_minutes": round(state.preventive_duration, 6),
                    "age_before_hours": round(age_before, 6),
                    "age_after_hours": round(state.operating_hours[machine_index], 6),
                    "recovery_fraction": round(state.preventive_recovery, 6),
                    "technician_resource": "maintenance-team",
                    "synthetic": True,
                }
            )
        degraded = state.counts[machine_index] >= state.degradation_after
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
            failure_time = start
            age_before = state.operating_hours[machine_index]
            failure_id = f"FAIL-{len(self.failure_events) + 1:06d}"
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
                machine_instance_id=state.instance_ids[machine_index],
                failure_id=failure_id,
            )
            self._machine_state(
                state,
                machine_index,
                failure_time,
                "failed",
                job,
                state.repair_time,
            )
            self.failure_events.append(
                {
                    "failure_id": failure_id,
                    "machine_id": state.instance_ids[machine_index],
                    "process_node_id": state.machine_id,
                    "time_minutes": round(failure_time, 6),
                    "timestamp": self._timestamp(failure_time),
                    "job_id": job,
                    "failure_mode": (
                        "weibull_ageing" if state.failure_shape is not None else "legacy_random"
                    ),
                    "severity": min(5, max(1, round(1 + state.repair_time / 60))),
                    "downtime_minutes": round(state.repair_time, 6),
                    "failure_probability": round(failure_probability, 9),
                    "operating_age_hours": round(age_before, 6),
                    "synthetic": True,
                }
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
            self.maintenance_interventions.append(
                {
                    "intervention_id": f"CM-{len(self.maintenance_interventions) + 1:06d}",
                    "machine_id": state.instance_ids[machine_index],
                    "process_node_id": state.machine_id,
                    "time_minutes": round(failure_time, 6),
                    "timestamp": self._timestamp(failure_time),
                    "completed_at_minutes": round(start, 6),
                    "completed_at": self._timestamp(start),
                    "job_id": job,
                    "maintenance_type": "corrective",
                    "duration_minutes": round(state.repair_time, 6),
                    "age_before_hours": round(age_before, 6),
                    "age_after_hours": round(state.operating_hours[machine_index], 6),
                    "recovery_fraction": round(state.maintenance_recovery, 6),
                    "technician_resource": "maintenance-team",
                    "synthetic": True,
                }
            )
        end = start + duration
        load = min(1.0, wait / max(nominal, 1e-9))
        self._log(
            "operation_start",
            start,
            job,
            state.machine_id,
            shared_resource=state.shared_resource or "",
            machine_instance_id=state.instance_ids[machine_index],
        )
        self._machine_state(state, machine_index, start, "running", job, duration)
        energy = state.energy_kw * duration / 60 * (1 + 0.1 * load + (0.1 if degraded else 0))
        self._log(
            "operation_end",
            end,
            job,
            state.machine_id,
            duration,
            started_at=round(start, 6),
            energy=round(energy, 6),
            estimated_emissions_kg_co2e=round(
                energy * state.emission_factor_kg_co2e_per_kwh,
                6,
            ),
            cost=round(state.cost_per_hour * duration / 60, 6),
            degraded=degraded,
            machine_instance_id=state.instance_ids[machine_index],
        )
        state.available[machine_index] = end
        state.counts[machine_index] += 1
        state.operating_hours[machine_index] += duration / 60
        self._machine_state(state, machine_index, end, "idle")
        self._sensor_record(
            state,
            machine_index,
            end,
            job,
            load=load,
            degraded=degraded,
            failure_probability=failure_probability,
        )
        state.last_product_id = product_id
        self.last_load[state.machine_id] = load
        if shared is not None and shared_index is not None:
            shared[shared_index] = end
        return end

    def run(self) -> SimulationResult:
        started = perf_counter()
        jobs = []
        for state in self.machines.values():
            for instance_index in range(state.capacity):
                self._machine_state(state, instance_index, 0.0, "idle")
        for job in self._orders():
            product = self.products.get(job["product_id"], next(iter(self.products.values()), {}))
            route = self._route(product)
            if not route:
                raise ValueError("At least one process operation is required")
            cycle_times = mapping(product.get("cycle_time_minutes") or {})
            now, index, first_pass, lost, recycle_loop_count, quality_rejections = (
                float(job["release_time"]),
                0,
                True,
                False,
                0,
                0,
            )
            self._log("order_released", now, job["job_id"])
            self._wip(now, job["job_id"], job["product_id"], route[0], "released", 1)
            while index < len(route):
                state = self.machines[route[index]]
                duration = cycle_times.get(route[index])
                self._wip(
                    now,
                    job["job_id"],
                    job["product_id"],
                    state.machine_id,
                    "queued",
                )
                now = self._process(
                    state,
                    now,
                    job["job_id"],
                    job["product_id"],
                    float(duration) if duration is not None else None,
                )
                self._wip(
                    now,
                    job["job_id"],
                    job["product_id"],
                    state.machine_id,
                    "processed",
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
                        quality_rejections += 1
                        recycling_enabled = bool(
                            self.recycling
                            and self.recycling.get("enabled", False)
                            and self.recycling.get("source_node_id") == state.machine_id
                        )
                        recovery_yield = (
                            float(self.recycling.get("recovery_yield", 0.0))
                            if self.recycling
                            else 0.0
                        )
                        max_loops = int(self.recycling.get("max_loops", 0)) if self.recycling else 0
                        return_to = (
                            str(self.recycling.get("return_to_node_id", ""))
                            if self.recycling
                            else ""
                        )
                        quantity_unit = str(
                            (self.recycling or {}).get(
                                "quantity_unit",
                                product.get("unit") or "unit",
                            )
                        )
                        eligible = recycling_enabled and recycle_loop_count < max_loops
                        recovered = eligible and self.random.random() < recovery_yield
                        if recovered:
                            if return_to not in route:
                                raise ValueError(
                                    "Recycling return node is absent from the product routing: "
                                    f"{return_to!r}"
                                )
                            recycle_loop_count += 1
                            outcome = "recycled"
                            recovered_quantity = 1.0
                            unrecoverable_quantity = 0.0
                        elif recycling_enabled and recycle_loop_count >= max_loops:
                            outcome = "max_loops_reached"
                            recovered_quantity = 0.0
                            unrecoverable_quantity = 1.0
                        elif recycling_enabled:
                            outcome = "recovery_loss"
                            recovered_quantity = 0.0
                            unrecoverable_quantity = 1.0
                        elif self.recycling:
                            outcome = "disabled_final_loss"
                            recovered_quantity = 0.0
                            unrecoverable_quantity = 1.0
                        else:
                            outcome = "not_configured_final_loss"
                            recovered_quantity = 0.0
                            unrecoverable_quantity = 1.0
                        recycling_id = f"REC-{len(self.recycling_records) + 1:06d}"
                        recycling_record = {
                            "recycling_event_id": recycling_id,
                            "time_minutes": round(now, 6),
                            "timestamp": self._timestamp(now),
                            "job_id": job["job_id"],
                            "product_id": job["product_id"],
                            "source_node_id": state.machine_id,
                            "return_to_node_id": return_to,
                            "quality_rejection_number": quality_rejections,
                            "completed_recycle_loops": recycle_loop_count,
                            "max_recycle_loops": max_loops,
                            "input_quantity": 1.0,
                            "recovered_quantity": recovered_quantity,
                            "unrecoverable_quantity": unrecoverable_quantity,
                            "quantity_unit": quantity_unit,
                            "configured_recovery_yield": recovery_yield,
                            "recovery_attempted": eligible,
                            "outcome": outcome,
                            "synthetic": True,
                        }
                        self.recycling_records.append(recycling_record)
                        self._log(
                            "recycling_return" if recovered else "recycling_final_loss",
                            now,
                            job["job_id"],
                            state.machine_id,
                            recycling_event_id=recycling_id,
                            return_to_node_id=return_to,
                            recycle_loop_count=recycle_loop_count,
                            recovered_quantity=recovered_quantity,
                            unrecoverable_quantity=unrecoverable_quantity,
                            quantity_unit=quantity_unit,
                            outcome=outcome,
                        )
                        if recovered:
                            self._wip(
                                now,
                                job["job_id"],
                                job["product_id"],
                                return_to,
                                "recycling_return",
                            )
                            index = route.index(return_to)
                            continue
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
            self._wip(
                now,
                job["job_id"],
                job["product_id"],
                route[min(index, len(route) - 1)],
                "lost" if lost else "completed",
                -1,
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
                    "final_material_loss": 1 if lost else 0,
                    "recycled_quantity": recycle_loop_count,
                    "recycle_loop_count": recycle_loop_count,
                    "quality_rejections": quality_rejections,
                    "material_balance_error": 0.0,
                }
            )
        self.events.sort(key=lambda event: (event["time"], event["event_id"]))
        for number, event in enumerate(self.events, 1):
            event["event_id"] = number
        self.machine_states.sort(
            key=lambda row: (float(row["time_minutes"]), str(row["machine_id"]), str(row["status"]))
        )
        self.sensor_records.sort(
            key=lambda row: (float(row["time_minutes"]), str(row["machine_id"]))
        )
        self.failure_events.sort(key=lambda row: (float(row["time_minutes"]), row["failure_id"]))
        self.maintenance_interventions.sort(
            key=lambda row: (float(row["time_minutes"]), row["intervention_id"])
        )
        self.queue_history.sort(
            key=lambda row: (float(row["time_minutes"]), str(row["machine_id"]), str(row["job_id"]))
        )
        self.work_in_progress.sort(
            key=lambda row: (float(row["time_minutes"]), str(row["job_id"]), str(row["status"]))
        )
        self.recycling_records.sort(
            key=lambda row: (float(row["time_minutes"]), str(row["recycling_event_id"]))
        )
        materials: dict[str, float] = {}
        finished_goods: dict[str, int] = {}
        measured_losses: dict[str, int] = {}
        recycled_throughput: dict[str, int] = {}
        for job in jobs:
            product = self.products.get(str(job["product_id"]), {})
            for material, quantity in mapping(product.get("bill_of_materials") or {}).items():
                materials[str(material)] = materials.get(str(material), 0.0) + float(quantity)
            destination = finished_goods if job.get("accepted", True) else measured_losses
            product_id = str(job["product_id"] or "unspecified")
            destination[product_id] = destination.get(product_id, 0) + 1
            recycled_throughput[product_id] = recycled_throughput.get(product_id, 0) + int(
                job.get("recycled_quantity", 0)
            )
        released_quantity = len(jobs)
        accepted_quantity = sum(bool(job.get("accepted", True)) for job in jobs)
        final_loss_quantity = sum(float(job.get("final_material_loss", 0)) for job in jobs)
        recycled_quantity = sum(float(job.get("recycled_quantity", 0)) for job in jobs)
        material_balance_error = released_quantity - accepted_quantity - final_loss_quantity
        final_state = {
            "time_minutes": round(
                max((float(job["completion_time"]) for job in jobs), default=0.0), 6
            ),
            "timestamp": self._timestamp(
                max((float(job["completion_time"]) for job in jobs), default=0.0)
            ),
            "machines": {
                instance_id: {
                    "process_node_id": state.machine_id,
                    "status": "idle",
                    "operating_age_hours": round(state.operating_hours[index], 6),
                    "completed_cycles": state.counts[index],
                    "available_at_minutes": round(state.available[index], 6),
                }
                for state in self.machines.values()
                for index, instance_id in enumerate(state.instance_ids[: state.capacity])
            },
            "queues": {
                machine_id: {
                    "queued_jobs": 0,
                    "buffer_capacity": state.buffer_capacity,
                    "next_available_minutes": round(min(state.available), 6),
                }
                for machine_id, state in self.machines.items()
            },
            "work_in_progress": self.current_wip,
            "inventories": {
                "material_consumed": {key: round(value, 6) for key, value in materials.items()},
                "finished_goods": finished_goods,
                "measured_losses": measured_losses,
                "recycled_throughput": recycled_throughput,
                "constraint_mode": "accounting_only_no_stock_capacity",
            },
            "totals": {
                "released_quantity": released_quantity,
                "accepted_quantity": accepted_quantity,
                "recycled_quantity": recycled_quantity,
                "final_material_loss_quantity": final_loss_quantity,
                "material_balance_error": material_balance_error,
                "quality_rejections": sum(int(job.get("quality_rejections", 0)) for job in jobs),
                "recycling_attempts": sum(
                    bool(record.get("recovery_attempted", False))
                    for record in self.recycling_records
                ),
                "energy_kwh": round(
                    sum(
                        float(event.get("energy", 0))
                        for event in self.events
                        if event["event_type"] == "operation_end"
                    ),
                    6,
                ),
                "estimated_emissions_kg_co2e": round(
                    sum(
                        float(event.get("estimated_emissions_kg_co2e", 0)) for event in self.events
                    ),
                    6,
                ),
                "production_cost": round(
                    sum(float(event.get("cost", 0)) for event in self.events),
                    6,
                ),
            },
        }
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
                "code_version": "0.4.0",
                "time_unit": "minute",
                "operating_age_unit": "hour",
                "sensor_data_classification": "synthetic_hypothesis_not_calibrated",
                "maintenance_policy": {
                    "corrective": "enabled_after_simulated_failure",
                    "preventive": "configured_per_machine_or_machine_type_by_age_or_degradation",
                    "technician_resource": "maintenance-team",
                },
                "recycling_policy": {
                    "enabled": bool(self.recycling and self.recycling.get("enabled", False)),
                    "source_node_id": (self.recycling or {}).get("source_node_id"),
                    "return_to_node_id": (self.recycling or {}).get("return_to_node_id"),
                    "configured_recovery_yield": (self.recycling or {}).get("recovery_yield"),
                    "max_loops": (self.recycling or {}).get("max_loops"),
                    "atomic_yield_interpretation": "seeded_bernoulli_per_rejected_unit",
                },
                "model_limits": {
                    "resource_calendars": "declared_not_enforced",
                    "human_capacity": "not_constrained",
                    "stock_capacity": "accounting_only_not_constrained",
                    "energy_tariffs": "constant_machine_cost_only",
                    "failure_timing": "evaluated_before_operation_not_mid_operation",
                    "repair_duration": "deterministic",
                    "material_balance": (
                        "unit_level_conservation_with_internal_recycled_throughput; "
                        "bill_of_materials_not_continuous_mass_balance"
                    ),
                },
            },
            machine_states=self.machine_states,
            sensor_records=self.sensor_records,
            failure_events=self.failure_events,
            maintenance_interventions=self.maintenance_interventions,
            queue_history=self.queue_history,
            work_in_progress=self.work_in_progress,
            recycling_records=self.recycling_records,
            final_state=final_state,
        )


def simulate(factory: Any, scenario: Any, product: Any | None = None) -> SimulationResult:
    return DigitalTwinSimulator(factory, scenario, product).run()
