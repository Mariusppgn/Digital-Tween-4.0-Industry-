# SylvaPapers — Module catalog

## 1. Shared contracts

| Field | Value |
|---|---|
| Objective | Validate factory, production, reliability, maintenance and future-module exchanges. |
| Inputs | YAML/JSON configuration and persisted result records. |
| Outputs | Strict typed models and JSON Schemas. |
| Dependency rule | No import from a business module. |
| Status | Implemented and tested; extension points prepared for Modules C–E. |

## 2. Module A — digital twin

| Field | Value |
|---|---|
| Objective | Simulate the paper mill and produce auditable operational and condition evidence. |
| Inputs | Factory graph, products, orders, seed, horizon and synthetic parameters. |
| Methods | Discrete-event simulation, NetworkX routes and two-parameter Weibull reliability. |
| Outputs | Events, jobs, states, sensors, failures, maintenance, queues, WIP, KPI, figures and final state. |
| Budget | `fast` < 30 s for a simple run; `standard` < 2 min for a monthly study. |
| Status | Implemented and tested synthetic baseline. |

## 3. Module B — predictive maintenance

| Field | Value |
|---|---|
| Objective | Rank machine risk and compare maintenance policies using Module A evidence. |
| Inputs | States, sensors, failures, interventions, machine types, horizon and costs. |
| Methods | EWMA, robust threshold, conditional Weibull risk, RUL and economic baselines. |
| Outputs | Condition scores, alerts, risk, RUL uncertainty, recommendations, policy costs and figures. |
| Budget | `fast` < 30 s; optional research comparisons < 5 min per default configuration. |
| Status | Implemented and tested interpretable synthetic baseline. |

## 4. Factory editor

| Field | Value |
|---|---|
| Objective | Edit steps, materials, machines, relations and Weibull coefficients visually. |
| Interface | Local French web application with keyboard support. |
| Persistence | Validated JSON import/export and explicit atomic YAML/JSON write. |
| Status | Implemented and browser-validated. |

## 5. Module C — resource allocation

| Field | Value |
|---|---|
| Objective | Schedule production, operators, technicians and maintenance windows. |
| Prepared inputs | Orders, machine states, capacities and Module B recommendations. |
| Planned baseline | Greedy reference followed by CP-SAT or MILP comparison. |
| Status | Public contracts and A/B handoff prepared; optimizer not implemented. |

## 6. Module D — marketing optimization

| Field | Value |
|---|---|
| Objective | Optimize demand generation without exceeding feasible factory capacity. |
| Prepared inputs | Demand, margins, Module A service, cost and capacity evidence. |
| Planned baseline | Saturation/adstock contribution model and constrained allocation. |
| Status | Public contracts prepared; model not implemented. |

## 7. Module E — R&D portfolio

| Field | Value |
|---|---|
| Objective | Select parameter-changing improvements under budget, resources and uncertainty. |
| Prepared inputs | Module A bottlenecks and risks plus Module D market value. |
| Planned baseline | Expected-value reference, Monte Carlo and multiobjective selection. |
| Status | Public contracts prepared; model not implemented. |

## 8. Separation rule

Each module has a business problem, declared inputs and outputs, example data, tests and figures. The
monorepo is a delivery choice, not permission for uncontrolled cross-imports. Future extraction must
preserve schema versions, units, provenance and technical English identifiers.
