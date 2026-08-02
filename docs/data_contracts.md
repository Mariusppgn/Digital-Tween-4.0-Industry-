# SylvaPapers — Data contracts

## 1. Contract rules

`sylvapapers_contracts` uses strict Pydantic v2 models. Unknown fields are rejected, schema versions
use semantic-version strings, provenance labels distinguish synthetic assumptions from evidence, and
bounded collections and numbers reduce malformed or excessive inputs.

## 2. Factory contracts

| Contract | Purpose | Key validation |
|---|---|---|
| `FactoryConfig` | factory identity, types, machines, graph and calendars | unique IDs and valid references |
| `MachineTypeConfig` | shared equipment reliability | unique type and Weibull density |
| `FailureDensityConfig` | two-parameter Weibull family | positive shape and scale hours |
| `MachineConfig` | physical equipment capacity and metadata | positive capacity and declared type |
| `ProcessGraph` | editable process topology | unique nodes and non-dangling edges |
| `ProcessNode` | step, materials and editor position | operation references declared machines |
| `ProcessEdge` | directed material relation | valid source/target and bounded probability |

## 3. Scenario contracts

| Contract | Purpose | Key validation |
|---|---|---|
| `ProductDefinition` | enabled state, recipe, timings and bill of materials | positive values; routing may be derived |
| `ProductionOrder` | dated roll demand | bounded positive quantity and valid dates |
| `SimulationScenario` | products, orders, seed and horizon | known enabled products only |

## 4. Module A operational contracts

| Contract | Purpose | Key validation |
|---|---|---|
| `SimulationEvent` | unified event journal | timestamp, entity identity and non-negative duration |
| `MachineState` | status and utilization snapshot | bounded utilization and non-negative operating age |
| `SensorRecord` | multivariate machine observation | values and units have identical bounded keys |
| `FailureEvent` | failure outcome and downtime | severity 1–5 and bounded sensor context |
| `KPIReport` | versioned aggregate metrics | explicit metric names, values and units |

Module A persists these contracts to `machine_states.csv`, `sensors.csv` and `failures.csv`, with
maintenance, queue, WIP, event, job, KPI, summary and final-state artefacts in the same result bundle.

## 5. Module B configuration contracts

| Contract | Purpose | Key validation |
|---|---|---|
| `MaintenanceAnalysisConfig` | horizon, EWMA, robust threshold, confidence and failure densities | finite bounded values and explicit Weibull defaults |
| `MaintenanceEconomicConfig` | corrective, preventive and predictive cost assumptions | non-negative costs/downtime and bounded effectiveness |

The baseline configuration is explicitly marked `synthetic_example`. Currency, cost and effectiveness
parameters cannot be interpreted as observed mill economics.

## 6. Module B result contracts

| Contract | Purpose | Key validation |
|---|---|---|
| `AnomalyResult` | latest EWMA robust anomaly and variable importance | non-negative score and importance in [0, 1] |
| `ReliabilityEstimate` | conditional Weibull risk and RUL interval | probabilities bounded and interval contains estimate |
| `MaintenancePolicyCost` | expected policy cost and downtime | exactly named policy and non-negative outcomes |
| `MaintenanceRecommendation` | action, urgency, window, confidence and reasons | complete ordered window and bounded importance |
| `MaintenanceAssessment` | decision-ready machine-level aggregate | consistent machine ID and three unique policies |

Module B persists `maintenance_assessments.json`, `maintenance_policy_costs.csv`,
`sensor_anomalies.png`, `failure_risk_rul.png` and `maintenance_policy_costs.png`.

## 7. Future-module contracts

`ProductionSchedule`, `MarketingPlan`, `DemandForecast`, `RDProject` and `RDPortfolio` remain
public versioned boundaries for Modules C–E. Their existence does not mean the corresponding
optimizers are implemented.

## 8. Interoperability rule

Modules exchange validated files and contract models, not private classes or mutable runtime state.
Technical identifiers remain English; documentation and user-facing descriptions may be French.
Every numeric field requires an explicit unit or an unambiguous contract-defined unit.

## 9. Schema generation

```bash
uv run python -c "from sylvapapers_contracts import export_json_schemas; export_json_schemas('schemas')"
```

Generated schemas are deterministic review artefacts and must be refreshed after contract changes.
