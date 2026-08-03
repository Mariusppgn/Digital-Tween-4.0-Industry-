"""Versioned data contracts shared by the SylvaPapers digital-twin modules."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from math import exp, inf
from math import pow as float_power
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractModel(BaseModel):
    """Strict, serialisable base for all public contracts."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        allow_inf_nan=False,
    )

    schema_version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    provenance: str = Field(default="sylvapapers", min_length=1)


class MachineStatus(StrEnum):
    IDLE = "idle"
    SETUP = "setup"
    RUNNING = "running"
    BLOCKED = "blocked"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


class GraphPosition(BaseModel):
    """Editor coordinates persisted with a process step."""

    model_config = ConfigDict(extra="forbid")

    x: float
    y: float


class ProcessNode(ContractModel):
    node_id: str = Field(min_length=1)
    kind: Literal["source", "operation", "buffer", "quality_control", "sink"]
    name: str = Field(min_length=1)
    machine_ids: list[str] = Field(default_factory=list)
    capacity: float | None = Field(default=None, gt=0)
    capacity_unit: str | None = None
    input_materials: list[str] = Field(default_factory=list)
    output_materials: list[str] = Field(default_factory=list)
    position: GraphPosition | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

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
    relation: Literal["forward", "recycle"] = "forward"
    condition: str | None = None
    probability: float | None = Field(default=None, ge=0, le=1)
    material: str | None = None


class RecyclingConfig(ContractModel):
    """Bounded quality-loss feedback configured on the process graph.

    ``recovery_yield`` is interpreted as a Bernoulli recovery probability for
    each atomic simulation unit. Its aggregate realised yield converges to the
    configured value over a sufficiently long seeded simulation campaign.
    """

    enabled: bool = False
    source_node_id: str = Field(min_length=1)
    return_to_node_id: str = Field(min_length=1)
    recovery_yield: float = Field(default=0.75, ge=0, le=1)
    max_loops: int = Field(default=1, ge=1, le=20)
    quantity_unit: str = Field(default="roll_equivalent", min_length=1)
    assumptions_are_synthetic: bool = True


class ProcessGraph(ContractModel):
    nodes: list[ProcessNode] = Field(min_length=2)
    edges: list[ProcessEdge] = Field(min_length=1)
    recycling: RecyclingConfig | None = None

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
        recycle_edges = [edge for edge in self.edges if edge.relation == "recycle"]
        if len(recycle_edges) > 1:
            raise ValueError("only one controlled recycling edge is supported")
        if recycle_edges and self.recycling is None:
            raise ValueError("a recycle edge requires an explicit recycling configuration")
        if self.recycling is not None:
            if len(recycle_edges) != 1:
                raise ValueError("recycling configuration requires exactly one recycle edge")
            recycle_edge = recycle_edges[0]
            expected = (
                self.recycling.source_node_id,
                self.recycling.return_to_node_id,
            )
            if (recycle_edge.source, recycle_edge.target) != expected:
                raise ValueError("recycle edge endpoints must match the recycling configuration")
            nodes = {node.node_id: node for node in self.nodes}
            if nodes[recycle_edge.source].kind != "quality_control":
                raise ValueError("recycling must originate from a quality-control node")
            if nodes[recycle_edge.target].kind != "operation":
                raise ValueError("recycling must return to an operation node")

        forward_adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
        for edge in self.edges:
            if edge.relation == "forward":
                forward_adjacency[edge.source].append(edge.target)
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visiting:
                raise ValueError("forward process edges must form an acyclic graph")
            if node_id in visited:
                return
            visiting.add(node_id)
            for target in forward_adjacency[node_id]:
                visit(target)
            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in node_ids:
            visit(node_id)
        if self.recycling is not None:
            reachable = {self.recycling.return_to_node_id}
            pending = [self.recycling.return_to_node_id]
            while pending:
                current = pending.pop()
                for target in forward_adjacency[current]:
                    if target not in reachable:
                        reachable.add(target)
                        pending.append(target)
            if self.recycling.source_node_id not in reachable:
                raise ValueError("recycle edge must return to an upstream operation")
        return self


class FailureDensityConfig(ContractModel):
    """Weibull time-to-failure density shared by one machine type.

    The two coefficients describe the density in operating hours. Reference
    configurations use synthetic hypotheses until observations are available
    for calibration.
    """

    family: Literal["weibull"] = "weibull"
    shape: float = Field(gt=0)
    scale_hours: float = Field(gt=0)

    def density_at(self, operating_hours: float) -> float:
        """Evaluate the configured probability density at an operating age."""

        if operating_hours < 0:
            raise ValueError("operating_hours must be non-negative")
        normalised_age = operating_hours / self.scale_hours
        if normalised_age == 0:
            if self.shape < 1:
                return inf
            if self.shape > 1:
                return 0.0
            return 1 / self.scale_hours
        return (
            (self.shape / self.scale_hours)
            * float_power(normalised_age, self.shape - 1)
            * exp(-float_power(normalised_age, self.shape))
        )


class MachineTypeConfig(ContractModel):
    """Parameters inherited by machines belonging to the same equipment type."""

    machine_type: str = Field(min_length=1)
    name: str = Field(min_length=1)
    failure_density: FailureDensityConfig
    metadata: dict[str, Any] = Field(default_factory=dict)


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
    machine_types: list[MachineTypeConfig] = Field(default_factory=list)
    machines: list[MachineConfig] = Field(min_length=1)
    process_graph: ProcessGraph
    resource_calendars: list[ResourceCalendar] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> FactoryConfig:
        machine_type_ids = [machine_type.machine_type for machine_type in self.machine_types]
        if len(machine_type_ids) != len(set(machine_type_ids)):
            raise ValueError("machine types must be unique")
        machine_ids = [machine.machine_id for machine in self.machines]
        if len(machine_ids) != len(set(machine_ids)):
            raise ValueError("machine ids must be unique")
        known = set(machine_ids)
        referenced = {
            machine_id for node in self.process_graph.nodes for machine_id in node.machine_ids
        }
        if unknown := referenced - known:
            raise ValueError(f"unknown machine ids in process graph: {sorted(unknown)}")
        if machine_type_ids:
            unknown_types = {machine.machine_type for machine in self.machines} - set(
                machine_type_ids
            )
            if unknown_types:
                raise ValueError(
                    f"machines reference unknown machine types: {sorted(unknown_types)}"
                )
        return self


class ProductDefinition(ContractModel):
    product_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    enabled: bool = True
    unit: str = Field(default="roll", min_length=1)
    routing: list[str] = Field(default_factory=list)
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
    quantity: int = Field(gt=0, le=100_000)
    quantity_unit: str = Field(default="roll", min_length=1)
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
    quantity_unit: str = Field(default="roll", min_length=1)


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
        disabled = {product.product_id for product in self.products if not product.enabled}
        if inactive := {order.product_id for order in self.orders} & disabled:
            raise ValueError(f"orders reference disabled products: {sorted(inactive)}")
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
    operating_age_hours: float | None = Field(default=None, ge=0)


class SensorRecord(ContractModel):
    sensor_id: str = Field(min_length=1)
    machine_id: str = Field(min_length=1)
    timestamp: datetime
    values: dict[str, float] = Field(min_length=1, max_length=64)
    units: dict[str, str] = Field(min_length=1, max_length=64)
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
    sensor_context: list[SensorRecord] = Field(default_factory=list, max_length=1_000)


class MaintenanceEconomicConfig(ContractModel):
    """Synthetic or calibrated cost assumptions used to compare policies."""

    currency: str = Field(default="EUR", min_length=3, max_length=3)
    corrective_intervention_cost: float = Field(default=8_000, ge=0)
    preventive_intervention_cost: float = Field(default=2_500, ge=0)
    predictive_intervention_cost: float = Field(default=3_000, ge=0)
    downtime_cost_per_hour: float = Field(default=1_500, ge=0)
    corrective_downtime_hours: float = Field(default=12, ge=0)
    planned_downtime_hours: float = Field(default=4, ge=0)
    predictive_effectiveness: float = Field(default=0.75, ge=0, le=1)
    preventive_age_recovery: float = Field(default=0.9, ge=0, le=1)
    assumptions_are_synthetic: bool = True


class MaintenanceAnalysisConfig(ContractModel):
    """Fast, interpretable baseline settings for predictive maintenance."""

    horizon_hours: float = Field(default=72, gt=0, le=8_760)
    ewma_alpha: float = Field(default=0.3, gt=0, le=1)
    robust_z_threshold: float = Field(default=3.5, gt=0, le=100)
    cusum_drift: float = Field(default=0.5, ge=0, le=100)
    cusum_threshold: float = Field(default=5.0, gt=0, le=1_000)
    minimum_baseline_points: int = Field(default=5, ge=3, le=10_000)
    calibration_bins: int = Field(default=5, ge=2, le=20)
    confidence_level: float = Field(default=0.8, gt=0, lt=1)
    predictive_risk_threshold: float = Field(default=0.25, gt=0, le=1)
    criticality: float = Field(default=1, gt=0, le=10)
    default_failure_density: FailureDensityConfig = Field(
        default_factory=lambda: FailureDensityConfig(shape=2, scale_hours=1_000)
    )
    machine_failure_densities: dict[str, FailureDensityConfig] = Field(
        default_factory=dict,
        max_length=10_000,
    )
    excluded_machine_ids: list[str] = Field(default_factory=list, max_length=10_000)
    economics: MaintenanceEconomicConfig = Field(default_factory=MaintenanceEconomicConfig)


class AnomalyResult(ContractModel):
    """Latest explainable anomaly score for one machine."""

    machine_id: str = Field(min_length=1)
    assessed_at: datetime
    method: Literal["ewma_robust", "cusum_robust"] = "ewma_robust"
    score: float = Field(ge=0)
    threshold: float = Field(gt=0)
    is_anomaly: bool
    observations_used: int = Field(ge=1, le=10_000_000)
    variable_importance: dict[str, float] = Field(default_factory=dict, max_length=64)

    @model_validator(mode="after")
    def validate_importance(self) -> AnomalyResult:
        if any(value < 0 or value > 1 for value in self.variable_importance.values()):
            raise ValueError("variable importance values must be between 0 and 1")
        return self


class ReliabilityEstimate(ContractModel):
    """Conditional Weibull risk and remaining-useful-life estimate."""

    machine_id: str = Field(min_length=1)
    assessed_at: datetime
    method: Literal["weibull_conditional"] = "weibull_conditional"
    operating_age_hours: float = Field(ge=0)
    horizon_hours: float = Field(gt=0, le=8_760)
    failure_probability: float = Field(ge=0, le=1)
    rul_hours: float = Field(ge=0)
    rul_lower_hours: float = Field(ge=0)
    rul_upper_hours: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_rul_interval(self) -> ReliabilityEstimate:
        if not self.rul_lower_hours <= self.rul_hours <= self.rul_upper_hours:
            raise ValueError("RUL interval must contain rul_hours")
        return self


class MaintenancePolicyCost(ContractModel):
    """Expected cost and downtime for one maintenance policy."""

    policy: Literal["corrective", "preventive", "predictive"]
    expected_cost: float = Field(ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    expected_downtime_hours: float = Field(ge=0)
    intervention_probability: float = Field(ge=0, le=1)
    assumptions_are_synthetic: bool = True
    rationale: list[str] = Field(default_factory=list, max_length=20)


class MaintenanceIntervention(ContractModel):
    """Completed maintenance action exported by Module A."""

    intervention_id: str = Field(min_length=1)
    machine_id: str = Field(min_length=1)
    maintenance_type: Literal["corrective", "preventive", "predictive"]
    started_at: datetime
    completed_at: datetime
    duration_minutes: float = Field(ge=0)
    age_before_hours: float = Field(ge=0)
    age_after_hours: float = Field(ge=0)
    recovery_fraction: float = Field(ge=0, le=1)
    technician_resource: str = Field(min_length=1)
    synthetic: bool = True

    @model_validator(mode="after")
    def validate_intervention(self) -> MaintenanceIntervention:
        if self.completed_at < self.started_at:
            raise ValueError("maintenance completion cannot precede its start")
        if self.age_after_hours > self.age_before_hours:
            raise ValueError("maintenance cannot increase operating age")
        return self


class MaintenanceRecommendation(ContractModel):
    recommendation_id: str = Field(min_length=1)
    machine_id: str = Field(min_length=1)
    created_at: datetime
    action: str = Field(min_length=1)
    urgency: Literal["low", "medium", "high", "critical"]
    confidence: float = Field(ge=0, le=1)
    due_at: datetime | None = None
    policy: Literal["corrective", "preventive", "predictive"] | None = None
    intervention_window_start: datetime | None = None
    intervention_window_end: datetime | None = None
    variable_importance: dict[str, float] = Field(default_factory=dict, max_length=64)
    expected_cost: float | None = Field(default=None, ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    rationale: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_intervention_window(self) -> MaintenanceRecommendation:
        start = self.intervention_window_start
        end = self.intervention_window_end
        if (start is None) != (end is None):
            raise ValueError("both intervention window bounds must be supplied together")
        if start is not None and end is not None and end <= start:
            raise ValueError("intervention window end must be later than its start")
        if any(value < 0 or value > 1 for value in self.variable_importance.values()):
            raise ValueError("variable importance values must be between 0 and 1")
        return self


class MaintenanceAssessment(ContractModel):
    """Decision-ready Module B output for one machine."""

    assessment_id: str = Field(min_length=1)
    machine_id: str = Field(min_length=1)
    created_at: datetime
    anomaly: AnomalyResult
    reliability: ReliabilityEstimate
    recommendation: MaintenanceRecommendation
    policy_comparison: list[MaintenancePolicyCost] = Field(min_length=3, max_length=3)
    data_provenance: Literal["module_a", "external", "synthetic_example"]

    @model_validator(mode="after")
    def validate_consistency(self) -> MaintenanceAssessment:
        machine_ids = {
            self.machine_id,
            self.anomaly.machine_id,
            self.reliability.machine_id,
            self.recommendation.machine_id,
        }
        if len(machine_ids) != 1:
            raise ValueError("maintenance assessment machine ids must match")
        policies = [item.policy for item in self.policy_comparison]
        if set(policies) != {"corrective", "preventive", "predictive"}:
            raise ValueError("policy comparison must contain each maintenance policy once")
        if len(policies) != len(set(policies)):
            raise ValueError("maintenance policies must be unique")
        return self


class TemporalPrediction(ContractModel):
    """One leakage-free prediction evaluated against a future time window."""

    machine_id: str = Field(min_length=1)
    assessed_at: datetime
    method: Literal["ewma_robust", "cusum_robust"]
    anomaly_score: float = Field(ge=0)
    anomaly_threshold: float = Field(gt=0)
    is_alert: bool
    failure_probability: float = Field(ge=0, le=1)
    horizon_hours: float = Field(gt=0, le=8_760)
    observed_failure: bool | None = None
    is_censored: bool = False
    next_failure_at: datetime | None = None
    alert_lead_hours: float | None = Field(default=None, ge=0)
    observations_used: int = Field(ge=1, le=10_000_000)

    @model_validator(mode="after")
    def validate_outcome(self) -> TemporalPrediction:
        if self.is_censored != (self.observed_failure is None):
            raise ValueError("censored predictions must have an unknown observed_failure")
        if self.alert_lead_hours is not None and not (
            self.is_alert and self.observed_failure is True
        ):
            raise ValueError("alert lead time requires a true alert before a failure")
        return self


class TemporalValidationMetrics(ContractModel):
    """Temporal alert metrics computed without using future observations as features."""

    method: Literal["ewma_robust", "cusum_robust"]
    evaluated_points: int = Field(ge=0)
    censored_points: int = Field(ge=0)
    true_positive: int = Field(ge=0)
    false_positive: int = Field(ge=0)
    true_negative: int = Field(ge=0)
    false_negative: int = Field(ge=0)
    precision: float | None = Field(default=None, ge=0, le=1)
    recall: float | None = Field(default=None, ge=0, le=1)
    f1_score: float | None = Field(default=None, ge=0, le=1)
    brier_score: float | None = Field(default=None, ge=0, le=1)
    failure_events: int = Field(ge=0)
    detected_failure_events: int = Field(ge=0)
    missed_failure_events: int = Field(ge=0)
    mean_alert_lead_hours: float | None = Field(default=None, ge=0)
    median_alert_lead_hours: float | None = Field(default=None, ge=0)
    limitations: list[str] = Field(default_factory=list, max_length=20)


class ProbabilityCalibrationBin(ContractModel):
    """Observed frequency for one predicted-probability interval."""

    method: Literal["weibull_conditional"] = "weibull_conditional"
    bin_index: int = Field(ge=0)
    probability_lower: float = Field(ge=0, le=1)
    probability_upper: float = Field(ge=0, le=1)
    sample_count: int = Field(ge=1)
    mean_predicted_probability: float = Field(ge=0, le=1)
    observed_failure_rate: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_bin(self) -> ProbabilityCalibrationBin:
        if self.probability_upper <= self.probability_lower:
            raise ValueError("calibration bin upper bound must exceed its lower bound")
        return self


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
    quantity_unit: str = Field(default="roll", min_length=1)

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
