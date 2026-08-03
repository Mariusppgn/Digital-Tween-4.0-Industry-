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
| `RecyclingConfig` | controlled QC feedback | one QC source, upstream operation target, yield and bounded loops |

Forward edges remain acyclic. Exactly one explicitly typed `recycle` edge may close the controlled
quality loop when its `RecyclingConfig` is present. The reference yield is a Bernoulli probability
per `roll_equivalent`, not a continuous mass-yield coefficient.

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
maintenance, recycling, queue, WIP, event, job, KPI, summary and final-state artefacts in the same
result bundle.

## 5. Module A campaign exchange contracts

| Artefact | Grain | Compatibility role |
|---|---|---|
| `campaign_runs.csv` | replication | 21 KPI values, counts, seed, horizon and runtime |
| `kpi_statistics.csv` | KPI | n, mean, standard deviation, quantiles and 95% mean CI |
| `module_d_product_statistics.csv` | product × replication | portable capacity, service, loss and recycling evidence |
| `module_e_machine_statistics.csv` | machine × replication | portable utilization, reliability, energy, emissions and cost evidence |
| `column_dictionary.json` | table and column | data type, unit, description and flat-CSV compatibility declaration |

These exchange CSVs use schema version `1.0.0`, producer version `0.5.0`, UTF-8, a header row and
scalar cells. Each row has `schema_version`, `producer_version`, `data_classification`, `provenance`,
`campaign_id` and `scenario_id`; replicated tables also carry `replication` and `seed`.

## 6. Module B configuration contracts

| Contract | Purpose | Key validation |
|---|---|---|
| `MaintenanceAnalysisConfig` | horizon, EWMA/CUSUM thresholds, calibration bins, confidence and failure densities | finite bounded values and explicit Weibull defaults |
| `MaintenanceEconomicConfig` | corrective, preventive and predictive cost assumptions | non-negative costs/downtime and bounded effectiveness |

The baseline configuration is explicitly marked `synthetic_example`. Currency, cost and effectiveness
parameters cannot be interpreted as observed mill economics.

## 7. Module B result contracts

| Contract | Purpose | Key validation |
|---|---|---|
| `AnomalyResult` | latest EWMA or CUSUM robust anomaly and variable importance | non-negative score and importance in [0, 1] |
| `ReliabilityEstimate` | conditional Weibull risk and RUL interval | probabilities bounded and interval contains estimate |
| `MaintenancePolicyCost` | expected policy cost and downtime | exactly named policy and non-negative outcomes |
| `MaintenanceRecommendation` | action, urgency, window, confidence and reasons | complete ordered window and bounded importance |
| `MaintenanceAssessment` | decision-ready machine-level aggregate | consistent machine ID and three unique policies |
| `TemporalPrediction` | one rolling-origin prediction, outcome and censoring state | complete outcome/censoring consistency and explicit units at export |
| `TemporalValidationMetrics` | temporal confusion, Brier score and event lead-time summary | non-negative counts and bounded optional scores |
| `ProbabilityCalibrationBin` | predicted risk versus observed frequency | ordered probability bounds and non-empty sample count |

Module B additionally persists flat, versioned `temporal_predictions.csv`,
`temporal_validation_metrics.csv`, `probability_calibration.csv` and
`machine_decision_features.csv`. `module_b_manifest.json` records source versions, provenance,
classification, units, filenames and limitations for consumers in separate repositories.

## 8. Future-module contracts

`ProductionSchedule`, `MarketingPlan`, `DemandForecast`, `RDProject` and `RDPortfolio` remain
public versioned boundaries for Modules C–E. Their existence does not mean the corresponding
optimizers are implemented.

## 9. Interoperability rule

Modules exchange validated files and contract models, not private classes or mutable runtime state.
Technical identifiers remain English; documentation and user-facing descriptions may be French.
Every numeric field requires an explicit unit or an unambiguous contract-defined unit.

Modules D and E will be separate repositories. They must consume copied exchange files plus their
adjacent dictionary or manifest, reject incompatible major schema versions and never import this
repository's private Python modules. The full handoff is defined in `inter_repository_exports.md`.

## 10. Schema generation

```bash
uv run python -c "from sylvapapers_contracts import export_json_schemas; export_json_schemas('schemas')"
```

Generated schemas are deterministic review artefacts and must be refreshed after contract changes.
