# Module catalogue

## 1. `asteria-contracts`

| Dimension | First-delivery definition |
|---|---|
| Objective | Provide versioned, unit-aware and provenance-aware exchange contracts. |
| Inputs | Python mappings, YAML and JSON documents. |
| Outputs | Validated Pydantic objects and JSON Schemas. |
| Baseline algorithms | Pydantic v2 validation and deterministic serialization. |
| Advanced extensions | Compatibility migration and semantic validation across schema versions. |
| Visualizations | Contract relationship diagram and schema coverage matrix. |
| Dependencies | Pydantic and PyYAML only; no business-package dependency. |
| Validation criteria | Positive and negative examples, reference checks, unit checks and 19 schema exports. |
| Compute budget | Less than 1 second for the reference configuration. |

## 2. `asteria-digital-twin`

| Dimension | First-delivery definition |
|---|---|
| Objective | Simulate the composite-panel factory and generate shared operational evidence. |
| Inputs | Factory graph, products, orders, calendars, quality, failure, energy and seed parameters. |
| Outputs | Event log, job history, KPI report, reproducibility metadata and figures. |
| Baseline algorithms | Seeded lightweight discrete-event scheduling with finite capacities and bounded rework. |
| Advanced extensions | SimPy engine, scenario ensembles, robust policies and calibrated degradation. |
| Visualizations | Process graph, Gantt, queues, cumulative output, utilization, energy and KPI dashboard. |
| Dependencies | `asteria-contracts`, NetworkX and Matplotlib; SimPy is reserved for the richer engine. |
| Validation criteria | Determinism, series/parallel/rework topology, capacity invariants, non-negative values and ten KPI. |
| Compute budget | Fast run below 30 seconds; standard monthly replications below 2 minutes. |

## 3. `asteria-predictive-maintenance`

| Dimension | First-delivery definition |
|---|---|
| Objective | Estimate failure risk and compare corrective, preventive and predictive policies. |
| Inputs | Sensor records, cycles, load, machine states, failures, maintenance history and costs. |
| Outputs | Anomaly scores, failure probabilities, RUL intervals and maintenance recommendations. |
| Baseline algorithms | Physical thresholds, EWMA, CUSUM and Weibull survival. |
| Advanced extensions | Cox models, state-space models, conformal prediction and calibrated boosting. |
| Visualizations | Annotated signals, survival/calibration curves, precision-recall and policy cost comparison. |
| Dependencies | `asteria-contracts`; consumes digital-twin artefacts without importing its internals. |
| Validation criteria | Time-aware split, calibration, no leakage and measurable cost gain over simple policies. |
| Compute budget | Standard fit and evaluation below 60 seconds; research methods below 5 minutes. |

## 4. `asteria-resource-allocation`

| Dimension | First-delivery definition |
|---|---|
| Objective | Allocate operators, technicians, machines and maintenance windows feasibly. |
| Inputs | Orders, routes, skills, calendars, capacity, predicted outages, priorities and energy constraints. |
| Outputs | Production schedule, assignments, maintenance slots, delays, cost and robustness indicators. |
| Baseline algorithms | Greedy feasible scheduler followed by CP-SAT comparison. |
| Advanced extensions | Robust/scenario optimization and local search. |
| Visualizations | Gantt, resource heatmap, capacity-demand and cost-delay frontier. |
| Dependencies | `asteria-contracts` and OR-Tools; results return to the twin as a versioned schedule. |
| Validation criteria | No hard-constraint violation and explicit comparison with the greedy baseline. |
| Compute budget | Fast baseline below 10 seconds; CP-SAT default below 2 minutes. |

## 5. `asteria-marketing-optimization`

| Dimension | First-delivery definition |
|---|---|
| Objective | Allocate marketing spend without exceeding feasible industrial capacity. |
| Inputs | Channel spend, demand, price, seasonality, margin, budget, service and capacity scenarios. |
| Outputs | Channel contribution, saturation, ROI, demand forecast and constrained budget recommendation. |
| Baseline algorithms | Adstock, saturation curves and constrained nonlinear allocation. |
| Advanced extensions | Bayesian MMM, causal analysis, contextual bandits and Bayesian optimization. |
| Visualizations | Contribution decomposition, saturation/adstock, ROI and revenue-capacity frontier. |
| Dependencies | `asteria-contracts`; consumes capacity KPI and emits demand contracts. |
| Validation criteria | Backtesting, uncertainty disclosure and no recommendation beyond service/capacity guardrails. |
| Compute budget | Standard baseline below 60 seconds; optional Bayesian run below 5 minutes. |

## 6. `asteria-rd-portfolio`

| Dimension | First-delivery definition |
|---|---|
| Objective | Select R&D projects under budget, skill, timing and risk constraints. |
| Inputs | Projects, dependencies, skills, probabilities, correlations, industrial KPI and market forecasts. |
| Outputs | Selected portfolio, allocation, schedule, value distribution, risk, Pareto frontier and opportunity cost. |
| Baseline algorithms | Integer programming and seeded Monte Carlo net-present-value simulation. |
| Advanced extensions | Robust multi-objective optimization, real options and value of information. |
| Visualizations | Risk-return matrix, Pareto frontier, budget/skill allocation, timeline and tornado chart. |
| Dependencies | `asteria-contracts`; consumes twin and marketing artefacts without direct package imports. |
| Validation criteria | Feasible dependencies and budgets, scenario stability and explicit comparison with value ranking. |
| Compute budget | Standard portfolio below 60 seconds; uncertainty study below 5 minutes. |

## 7. Cross-module acceptance

- Every module remains independently runnable with a small synthetic example.
- Every emitted artefact validates against a declared schema version.
- Advanced methods are optional and compared with the documented baseline.
- Integrated runs record configuration, seeds, versions, runtime, metrics and output paths.

