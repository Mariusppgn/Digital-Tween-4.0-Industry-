# SylvaPapers — Roadmap

## Status legend

- **Complete**: implemented with acceptance evidence in the repository.
- **Partial**: useful baseline exists, but a declared acceptance item remains.
- **Planned**: boundary is prepared but no implementation is claimed.

## Module A — paper-mill digital twin

| Increment | Status | Acceptance evidence |
|---|---|---|
| Versioned contracts and schemas | Complete | strict Pydantic validation and schema tests |
| Raw-wood to paper-roll graph | Complete | serial chain, three recipe branches and parallel machines |
| Editable steps, materials and relations | Complete | local graph editor with validated explicit write |
| Three activatable products | Complete | disabled-product order rejection |
| Two-parameter Weibull by machine type | Complete | density and conditional-risk tests |
| Independent physical machine state | Complete | machine-specific age, status and event identity |
| Seeded failures, repair and maintenance | Complete | reproducible failure and intervention records |
| Synthetic degradation and sensors | Complete | load, temperature, vibration, pressure, power, age and degradation |
| Queue and WIP instrumentation | Complete | timestamped queue and work-in-progress exports |
| Operational result bundle | Complete | states, sensors, failures, maintenance, recycling, KPI, figures and final state |
| Controlled QC recycling | Complete | QC → stock preparation, yield 0.75, two-loop bound and conservation tests |
| Long statistical campaign | Complete | 30 × 1,000 jobs, 15 KPI distributions, quantiles and 95% mean CI |
| Portable D/E evidence exports | Complete | product- and machine-level flat CSV plus column dictionary |
| Continuous dry-tonne balance | Planned | mass, moisture, yield and conservation tests |
| Full calendar and workforce enforcement | Planned | shifts, skills, planned stops and maintenance windows |
| Mid-operation interruption policies | Planned | resume, restart and scrap alternatives |

## Module B — predictive maintenance

| Increment | Status | Acceptance evidence |
|---|---|---|
| Versioned maintenance configuration | Complete | bounded horizon, thresholds, failure densities and costs |
| Module A bundle loader | Complete | explicit required files and malformed-input rejection |
| EWMA robust anomaly baseline | Complete | score, threshold, flag and variable importance |
| Conditional Weibull horizon risk | Complete | bounded probability from operating age |
| Weibull remaining useful life | Complete | estimate and containing uncertainty interval |
| Machine-level recommendations | Complete | urgency, policy, window, confidence and rationale |
| Policy economics | Complete | corrective, preventive and predictive expected cost/downtime |
| Deterministic output bundle | Complete | assessments, five interoperability CSVs, manifest and five figures |
| Censored-data Weibull fitting | Planned | approved history, estimator diagnostics and uncertainty |
| Time-aware backtesting | Complete baseline | rolling-origin prefixes, warning horizon and leakage controls |
| Right-censoring handling | Complete baseline | incomplete follow-up excluded from confusion and calibration |
| Probability calibration | Complete baseline | equal-width Weibull reliability bins and calibration figure |
| Temporal precision/recall evaluation | Complete baseline | EWMA/CUSUM confusion, F1, event recall and alert lead time |
| Advanced-method comparison | Partial | CUSUM implemented; Cox/state-space/ML candidates remain gated |

## Module A to B continuity

| Requirement | Status | Acceptance evidence |
|---|---|---|
| Public contract-only dependency | Complete | Module B does not import simulator internals |
| Persisted handoff | Complete | Module A outputs become validated Module B inputs |
| Reproducible command chain | Complete | validate → simulate → maintenance |
| Statistical campaign chain | Complete | campaign config → 30 replications → portable CSV and representative A bundle |
| Separate output directories | Complete | Module B cannot overwrite Module A evidence |
| Human approval boundary | Complete | recommendations are advisory and have no actuator path |
| Industrial calibration | Planned | approved mill data, governance and model monitoring |

## Compute and quality gates

| Profile | Intended scope | Guardrail |
|---|---|---:|
| `fast` | smoke simulation, one maintenance pass and tests | < 30 s per simple run; tests < 60 s |
| `standard` | monthly multi-replication study and policy comparison | < 2 min |
| `research` | optional sensitivity or advanced-method study | < 5 min per default configuration |

Each measured result must name hardware, Python version, scenario, seed, repetitions and output counts.
No planned algorithm may become a default without passing contracts, tests, Ruff, strict mypy,
reproducibility and bilingual documentation parity.

## Module C — resource allocation

| Task | Status | Dependency and acceptance target |
|---|---|---|
| Recommendation-to-window contract | Partial | consume Module B urgency and intervention window |
| Greedy scheduling baseline | Planned | feasible reference with explicit conflicts and costs |
| CP-SAT or MILP scheduler | Planned | compare against greedy under the same constraints |
| Maintenance and production co-scheduling | Planned | technicians, skills, shifts and machine capacity |
| Re-injection into Module A | Planned | simulate the schedule under seeded disruption |

## Module D — capacity-aware marketing

| Task | Status | Dependency and acceptance target |
|---|---|---|
| Demand and forecast contracts | Partial | versioned boundaries exist |
| Capacity evidence input | Complete boundary | consume `module_d_product_statistics.csv` and campaign KPI statistics |
| Maintenance capacity-risk input | Complete boundary | consume `machine_decision_features.csv` through its manifest |
| Synthetic channel history | Planned | provenance and units documented |
| Saturation and adstock baseline | Planned | interpretable contribution model |
| Constrained budget allocation | Planned | respect Module A capacity and service evidence |
| Counterfactual validation | Planned | compare demand, margin, delay and overload risk |

## Module E — R&D portfolio

| Task | Status | Dependency and acceptance target |
|---|---|---|
| Project and portfolio contracts | Partial | versioned boundaries exist |
| Machine evidence input | Complete boundary | consume `module_e_machine_statistics.csv` and campaign KPI statistics |
| Maintenance risk input | Complete boundary | consume `machine_decision_features.csv` through its manifest |
| Expected-value baseline | Planned | transparent costs, benefits and exclusions |
| Monte Carlo uncertainty | Planned | reproducible outcome distributions |
| Multiobjective selection | Planned | cost, value, energy, quality and risk frontier |
| Re-injection into Module A | Planned | selected projects change future factory parameters |

## Integrated scenarios

| Scenario | Status | Required modules |
|---|---|---|
| Baseline production and maintenance | Complete | A + B |
| Critical paper-machine degradation | Planned | A + B with calibrated event labels |
| Technician shortage | Planned | A + B + C |
| Energy-price increase | Planned | A + C |
| Capacity-aware marketing campaign | Planned | A + D |
| R&D project reducing drying time | Planned | A + E |
| Combined disruption portfolio | Planned | A + B + C + D + E |

No future increment may be presented as operationally calibrated without approved industrial data.
Modules D and E will be developed in separate repositories. Their first acceptance gate is successful
ingestion of the versioned flat exports without importing SylvaPapers A/B implementation packages.
