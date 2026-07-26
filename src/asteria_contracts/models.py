"""Versioned data contracts shared by the Asteria digital-twin modules."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractModel(BaseModel):
    """Strict, serialisable base for all public contracts."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    schema_version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    provenance: str = Field(default="asteria", min_length=1)


class MachineStatus(StrEnum):
    IDLE = "idle"
    SETUP = "setup"
    RUNNING = "running"
    BLOCKED = "blocked"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


class ProcessNode(ContractModel):
    node_id: str = Field(min_length=1)
    kind: Literal["source", "operation", "buffer", "quality_control", "rework", "sink"]
    name: str = Field(min_length=1)
    machine_ids: list[str] = Field(default_factory=list)
    capacity: float | None = Field(default=None, gt=0)
    capacity_unit: str | None = None

    @model_validator(mode="after")
    def validate_capacity(self) -> ProcessNode:
        if (self.capacity is None) != (self.capacity_unit is None):
            raise ValueError("capacity and capacity_unit must be supplied together")
        if self.kind == "operation" and not self.machine_ids:
            raise ValueError("an operation node must reference at least one machine")
        return self


class ProcessEdge(ContractModel):
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    condition: str | None = None
    probability: float | None = Field(default=None, ge=0, le=1)


class ProcessGraph(ContractModel):
    nodes: list[ProcessNode] = Field(min_length=2)
    edges: list[ProcessEdge] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_graph(self) -> ProcessGraph:
        node_ids = [node.node_id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("process node ids must be unique")
        known = set(node_ids)
        for edge in self.edges:
            if edge.source not in known or edge.target not in known:
                raise ValueError("process edges must reference existing nodes")
            if edge.source == edge.target:
                raise ValueError("self-loop process edges are not allowed")
        return self


class MachineConfig(ContractModel):
    machine_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    machine_type: str = Field(min_length=1)
    capabilities: list[str] = Field(min_length=1)
    capacity_per_hour: float = Field(gt=0)
    capacity_unit: str = Field(default="parts/hour", min_length=1)
    availability: float = Field(default=1.0, gt=0, le=1)
    mtbf_hours: float | None = Field(default=None, gt=0)
    mttr_hours: float | None = Field(default=None, gt=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResourceCalendar(ContractModel):
    resource_id: str = Field(min_length=1)
    timezone: str = Field(default="Europe/Paris", min_length=1)
    weekly_shifts: dict[str, list[str]] = Field(default_factory=dict)
    exceptions: dict[str, list[str]] = Field(default_factory=dict)


class FactoryConfig(ContractModel):
    factory_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    timezone: str = Field(default="Europe/Paris", min_length=1)
    machines: list[MachineConfig] = Field(min_length=1)
    process_graph: ProcessGraph
    resource_calendars: list[ResourceCalendar] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> FactoryConfig:
        machine_ids = [machine.machine_id for machine in self.machines]
        if len(machine_ids) != len(set(machine_ids)):
            raise ValueError("machine ids must be unique")
        known = set(machine_ids)
        referenced = {
            machine_id for node in self.process_graph.nodes for machine_id in node.machine_ids
        }
        if unknown := referenced - known:
            raise ValueError(f"unknown machine ids in process graph: {sorted(unknown)}")
        return self


class ProductDefinition(ContractModel):
    product_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    unit: str = Field(default="panel", min_length=1)
    routing: list[str] = Field(min_length=1)
    cycle_time_minutes: dict[str, float] = Field(default_factory=dict)
    bill_of_materials: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_positive_values(self) -> ProductDefinition:
        if any(value <= 0 for value in self.cycle_time_minutes.values()):
            raise ValueError("cycle times must be positive")
        if any(value <= 0 for value in self.bill_of_materials.values()):
            raise ValueError("bill-of-material quantities must be positive")
        return self


class ProductionOrder(ContractModel):
    order_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    quantity_unit: str = Field(default="panel", min_length=1)
    release_at: datetime
    due_at: datetime
    priority: int = Field(default=1, ge=1, le=10)

    @model_validator(mode="after")
    def validate_dates(self) -> ProductionOrder:
        if self.due_at <= self.release_at:
            raise ValueError("due_at must be later than release_at")
        return self


class DemandPoint(ContractModel):
    period_start: datetime
    product_id: str = Field(min_length=1)
    quantity: float = Field(ge=0)
    quantity_unit: str = Field(default="panel", min_length=1)


class DemandScenario(ContractModel):
    scenario_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    points: list[DemandPoint] = Field(min_length=1)


class SimulationScenario(ContractModel):
    scenario_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    factory_id: str = Field(min_length=1)
    start_at: datetime
    end_at: datetime
    products: list[ProductDefinition] = Field(min_length=1)
    orders: list[ProductionOrder] = Field(default_factory=list)
    demand: DemandScenario | None = None
    random_seed: int = Field(default=42, ge=0)
    fidelity: Literal["fast", "standard", "research"] = "fast"
    max_reworks: int = Field(default=1, ge=0, le=5)
    interarrival_time: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_scenario(self) -> SimulationScenario:
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be later than start_at")
        product_ids = [product.product_id for product in self.products]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("product ids must be unique")
        known = set(product_ids)
        if unknown := {order.product_id for order in self.orders} - known:
            raise ValueError(f"orders reference unknown products: {sorted(unknown)}")
        return self


class SimulationEvent(ContractModel):
    event_id: str = Field(min_length=1)
    timestamp: datetime
    event_type: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    duration_minutes: float | None = Field(default=None, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)


class MachineState(ContractModel):
    machine_id: str = Field(min_length=1)
    timestamp: datetime
    status: MachineStatus
    active_order_id: str | None = None
    utilisation: float = Field(default=0, ge=0, le=1)
    remaining_minutes: float | None = Field(default=None, ge=0)


class SensorRecord(ContractModel):
    sensor_id: str = Field(min_length=1)
    machine_id: str = Field(min_length=1)
    timestamp: datetime
    values: dict[str, float] = Field(min_length=1)
    units: dict[str, str] = Field(min_length=1)
    quality: Literal["good", "uncertain", "bad"] = "good"

    @model_validator(mode="after")
    def validate_units(self) -> SensorRecord:
        if set(self.values) != set(self.units):
            raise ValueError("every sensor value must have exactly one unit")
        return self


class FailureEvent(ContractModel):
    failure_id: str = Field(min_length=1)
    machine_id: str = Field(min_length=1)
    occurred_at: datetime
    failure_mode: str = Field(min_length=1)
    severity: int = Field(ge=1, le=5)
    downtime_minutes: float = Field(ge=0)
    sensor_context: list[SensorRecord] = Field(default_factory=list)


class MaintenanceRecommendation(ContractModel):
    recommendation_id: str = Field(min_length=1)
    machine_id: str = Field(min_length=1)
    created_at: datetime
    action: str = Field(min_length=1)
    urgency: Literal["low", "medium", "high", "critical"]
    confidence: float = Field(ge=0, le=1)
    due_at: datetime | None = None
    rationale: list[str] = Field(default_factory=list)


class ScheduleAssignment(ContractModel):
    order_id: str = Field(min_length=1)
    machine_id: str = Field(min_length=1)
    operation_id: str = Field(min_length=1)
    start_at: datetime
    end_at: datetime

    @model_validator(mode="after")
    def validate_window(self) -> ScheduleAssignment:
        if self.end_at <= self.start_at:
            raise ValueError("assignment end_at must be later than start_at")
        return self


class ProductionSchedule(ContractModel):
    schedule_id: str = Field(min_length=1)
    factory_id: str = Field(min_length=1)
    generated_at: datetime
    objective: str = Field(default="on_time_delivery", min_length=1)
    assignments: list[ScheduleAssignment] = Field(default_factory=list)


class MarketingCampaign(ContractModel):
    campaign_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    channel: str = Field(min_length=1)
    start_at: datetime
    end_at: datetime
    budget: float = Field(ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    expected_lift: float = Field(default=0, ge=-1)


class MarketingPlan(ContractModel):
    plan_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    campaigns: list[MarketingCampaign] = Field(default_factory=list)


class ForecastPoint(ContractModel):
    period_start: datetime
    product_id: str = Field(min_length=1)
    p10: float = Field(ge=0)
    p50: float = Field(ge=0)
    p90: float = Field(ge=0)
    quantity_unit: str = Field(default="panel", min_length=1)

    @model_validator(mode="after")
    def validate_quantiles(self) -> ForecastPoint:
        if not self.p10 <= self.p50 <= self.p90:
            raise ValueError("forecast quantiles must satisfy p10 <= p50 <= p90")
        return self


class DemandForecast(ContractModel):
    forecast_id: str = Field(min_length=1)
    generated_at: datetime
    horizon: str = Field(min_length=1)
    method: str = Field(min_length=1)
    points: list[ForecastPoint] = Field(min_length=1)


class RDProject(ContractModel):
    project_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    stage: Literal["idea", "feasibility", "prototype", "pilot", "industrialisation"]
    budget: float = Field(ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    start_at: datetime
    target_end_at: datetime
    technology_readiness_level: int = Field(ge=1, le=9)
    expected_value: float = Field(default=0, ge=0)


class RDPortfolio(ContractModel):
    portfolio_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    budget_limit: float = Field(gt=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    projects: list[RDProject] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_budget(self) -> RDPortfolio:
        if sum(project.budget for project in self.projects) > self.budget_limit:
            raise ValueError("R&D project budgets exceed the portfolio limit")
        return self


class KPIMetric(ContractModel):
    name: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)
    target: float | None = None


class KPIReport(ContractModel):
    report_id: str = Field(min_length=1)
    factory_id: str = Field(min_length=1)
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    metrics: list[KPIMetric] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_period(self) -> KPIReport:
        if self.period_end <= self.period_start:
            raise ValueError("period_end must be later than period_start")
        return self
