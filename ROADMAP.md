# Asteria Composites Lab — Roadmap

This roadmap turns the ecosystem vision into independently verifiable increments.
Difficulty uses a relative scale: **S** (small), **M** (medium), **L** (large).

## Delivery principles

- Each phase must keep the `fast` profile runnable on a laptop.
- Every advanced method must be compared with a transparent baseline.
- Synthetic values must remain labelled as assumptions, never as measured industrial data.
- Cross-module exchanges use versioned contracts instead of direct internal imports.
- English and French documentation must remain structurally equivalent.

## Phase 0 — Architecture and contracts

| Task | Objective | Dependencies | Difficulty | Acceptance criteria | Tests | Expected outputs |
|---|---|---|---:|---|---|---|
| P0.1 Architecture decisions | Define scope, module boundaries and dependency rules | None | S | Monorepo choice, risks and deferred decisions documented | Markdown/Mermaid render review | `docs/architecture*.md` |
| P0.2 Data contracts v0.1 | Establish typed, versioned exchange models | P0.1 | M | Required contracts validate examples and reject invalid units/relations | Contract and configuration tests | `asteria_contracts`, JSON schemas |
| P0.3 Minimal data | Provide a traceable factory and scenario example | P0.2 | S | Two products and a process graph with branching, parallelism and rework | YAML load and schema tests | `configs/`, `data/examples/` |
| P0.4 Development tooling | Make quality checks reproducible | None | S | Clean installation, lint, type-check and tests documented | CI workflow | `pyproject.toml`, CI, pre-commit |

## Phase 1 — Minimal industrial digital twin

| Task | Objective | Dependencies | Difficulty | Acceptance criteria | Tests | Expected outputs |
|---|---|---|---:|---|---|---|
| P1.1 Graph builder | Build the configurable manufacturing route | P0.2, P0.3 | M | Series, branch, two layup stations, shared preparation, bounded buffer and rework loop represented | Graph topology tests | NetworkX process graph |
| P1.2 Deterministic simulator | Execute orders with a fixed seed | P1.1 | L | Repeated runs produce identical events; no negative inventory or double booking | Determinism and invariants | Event log and final state |
| P1.3 Stochastic behaviour | Add cycle variability, quality, degradation, failures and maintenance | P1.2 | L | Probabilities remain bounded and maintenance reduces degradation | Boundary and seeded scenario tests | Synthetic machine and sensor events |

## Phase 2 — Instrumentation and KPI

| Task | Objective | Dependencies | Difficulty | Acceptance criteria | Tests | Expected outputs |
|---|---|---|---:|---|---|---|
| P2.1 Event persistence | Save reproducible simulation artefacts | P1.2 | M | Configuration, seed, schema/code version and runtime are recorded | Round-trip export tests | CSV/JSON output bundle |
| P2.2 KPI engine | Compute the ten initial operational metrics | P2.1 | M | KPI values are finite, unit-labelled and reconcile with events | Conservation/KPI fixture tests | `KPIReport` |
| P2.3 Figures and report | Generate graph, Gantt and KPI/energy figures | P2.1, P2.2 | M | Figures regenerate from one command without GUI | Smoke and file-signature tests | `reports/figures/`, report |
| P2.4 Compute benchmark | Protect laptop execution budgets | P1.2 | S | `fast` scenario completes below 30 seconds on reference CI | Timed smoke test | Benchmark JSON |

## Phase 3 — Degradation and predictive maintenance

| Task | Objective | Dependencies | Difficulty | Acceptance criteria | Tests | Expected outputs |
|---|---|---|---:|---|---|---|
| P3.1 Sensor generator | Produce contextual synthetic temperature, vibration and power signals | P1.3 | M | Signal provenance and assumptions documented | Distribution and seed tests | `SensorRecord` dataset |
| P3.2 Interpretable baseline | Compare thresholds, EWMA and Weibull risk | P3.1 | M | Temporal split, calibration and uncertainty reported | Leakage and metric tests | Risk scores and alerts |
| P3.3 Maintenance policy comparison | Compare corrective, preventive and predictive policies | P3.2 | L | Common cost horizon and uncertainty; no claim beyond synthetic evidence | Scenario regression tests | Cost-benefit report |

## Phase 4 — Resource allocation

| Task | Objective | Dependencies | Difficulty | Acceptance criteria | Tests | Expected outputs |
|---|---|---|---:|---|---|---|
| P4.1 Greedy scheduler | Establish an explainable planning baseline | P2.2 | M | Produces feasible operator and machine assignments | Constraint tests | Baseline schedule |
| P4.2 CP-SAT scheduler | Improve cost/service under capacity and skill constraints | P4.1, P3.3 | L | Feasible solution compared against greedy baseline | Feasibility/property tests | Optimized schedule |
| P4.3 Simulation feedback | Validate the schedule under stochastic disruption | P4.2 | L | Multiple seeds report robustness and failure modes | Scenario tests | Robustness indicators |

## Phase 5 — Capacity-aware marketing

| Task | Objective | Dependencies | Difficulty | Acceptance criteria | Tests | Expected outputs |
|---|---|---|---:|---|---|---|
| P5.1 Synthetic marketing generator | Create transparent channel, saturation and adstock data | P0.2 | M | Ground truth and generation seed recorded | Recovery fixture tests | Marketing dataset |
| P5.2 Contribution baseline | Estimate channel effects with uncertainty | P5.1 | L | Time-aware validation and identifiability caveats | Backtest tests | Contribution model |
| P5.3 Budget optimizer | Allocate spend within simulated factory capacity | P5.2, P2.2 | L | Recommendation respects budgets and service guardrails | Constraint tests | `MarketingPlan`, demand scenarios |

## Phase 6 — R&D portfolio

| Task | Objective | Dependencies | Difficulty | Acceptance criteria | Tests | Expected outputs |
|---|---|---|---:|---|---|---|
| P6.1 Project catalogue | Define synthetic projects, dependencies and uncertainty | P0.2 | M | Values labelled synthetic and correlations valid | Schema/PSD tests | R&D project dataset |
| P6.2 Portfolio baseline | Select projects under budget and skills | P6.1 | L | Feasible portfolio and explicit opportunity costs | Constraint tests | `RDPortfolio` |
| P6.3 Twin feedback | Apply selected improvements to future factory scenarios | P6.2, P2.2 | M | Parameter deltas are traceable and reversible | Before/after tests | Improved scenarios |

## Phase 7 — Integrated scenarios

| Task | Objective | Dependencies | Difficulty | Acceptance criteria | Tests | Expected outputs |
|---|---|---|---:|---|---|---|
| P7.1 Scenario catalogue | Cover demand, failure, energy, staffing and R&D disruptions | P3–P6 | M | Seven documented, reproducible scenarios | End-to-end smoke tests | Scenario library |
| P7.2 Comparative report | Explain operational and financial trade-offs | P7.1 | M | Same seeds, horizons and KPI definitions used | Report consistency tests | Integrated HTML/PDF report |
| P7.3 Lightweight dashboard | Make scenarios explorable without becoming core infrastructure | P7.1 | L | Simulation, comparison and export work locally | UI smoke test | Optional Streamlit app |

## Phase 8 — Advanced methods

| Task | Objective | Dependencies | Difficulty | Acceptance criteria | Tests | Expected outputs |
|---|---|---|---:|---|---|---|
| P8.1 Robust optimization | Quantify schedule and portfolio resilience | Validated baselines | L | Improvement measured against deterministic baseline | Stress tests | Robust solutions |
| P8.2 Calibrated uncertainty | Add conformal/state-space/Bayesian methods selectively | Validated baselines | L | Calibration and compute cost justify inclusion | Coverage tests | Uncertainty intervals |
| P8.3 Decision intelligence | Explore causal, bandit and value-of-information extensions | P5/P6 baselines | L | Explicit assumptions and baseline comparison | Offline policy tests | Research experiments |

