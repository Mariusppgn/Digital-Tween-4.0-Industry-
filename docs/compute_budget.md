# Compute budget

## 1. Purpose and scope

This budget keeps the first Asteria iteration fast, reproducible and usable on a normal developer laptop. It is an engineering guardrail, not a production SLA. The architecture remains a local Python monorepo; exceeding a budget first triggers profiling, algorithm/data-format improvements and reduced experiment scope—not a default move to microservices or distributed computing.

## 2. Reference environment

Budgets are measured on a reference class of machine, not a vendor model:

- 4 logical CPU cores available to the experiment;
- 8 GiB RAM available, with a 2 GiB soft cap per run;
- local SSD;
- supported 64-bit CPython;
- no required GPU;
- warm dependency cache and no network access during a run.

Benchmarks record CPU, RAM, Python/OS versions and cold/warm status. CI may use a smaller deterministic smoke profile; absolute timing assertions include a documented margin.

## 3. Workload classes

| Class | Intended use | Target wall time | Memory | Generated artefacts |
|---|---|---:|---:|---:|
| Unit | One function or micro-scenario | ≤ 1 s | ≤ 256 MiB | ≤ 1 MiB |
| Smoke | One small end-to-end module run | ≤ 10 s | ≤ 512 MiB | ≤ 10 MiB |
| Standard | One analyst scenario | ≤ 60 s | ≤ 1 GiB | ≤ 100 MiB |
| Integrated | Five-module first-iteration scenario | ≤ 180 s | ≤ 2 GiB | ≤ 250 MiB |
| Research batch | Explicit local campaign | ≤ 30 min | ≤ 4 GiB with opt-in | ≤ 2 GiB with retention plan |

Default commands run smoke or standard workloads. Research batches require explicit limits and must not run as part of ordinary tests.

## 4. Per-module budgets

| Module | Standard input envelope | Target | Hard first-iteration guardrail |
|---|---|---:|---:|
| Digital twin | ≤ 10,000 released parts, ≤ 1,000,000 events | 60 s / 1 GiB | 2,000,000 events or 120 s |
| Predictive maintenance | ≤ 100,000 observations, ≤ 200 features, ≤ 1,000 assets | 60 s / 1 GiB | 500,000 rows or 120 s |
| Resource allocation | ≤ 500 work items, ≤ 100 resources, ≤ 50,000 candidate assignments | 60 s / 1 GiB | solver timeout 120 s |
| Marketing optimisation | ≤ 100 segments × 30 channels × 20 scenarios | 30 s / 512 MiB | 120 s and bounded iterations |
| R&D portfolio | ≤ 500 projects, ≤ 2,000 dependency/constraint edges | 60 s / 1 GiB | solver timeout 120 s |

Crossing a guardrail returns a structured limit diagnostic before or during execution. Partial results are labelled incomplete and are never compared as successful experiments.

## 5. Digital-twin cost model

With a priority-queue event calendar, runtime should scale approximately with \(O(E \log E)\), where \(E\) is the number of emitted events; memory is \(O(E)\) only when retaining the full event log. Streaming KPI aggregation keeps live state proportional to active entities, queues and resources.

The default retains compact events required for audit and writes them in chunks. Queue snapshots at every event are prohibited; periodic or change-only snapshots are used. Autoclave batch selection must use bounded candidate scans. Termination guards cover horizon, event count, maximum rework and zero-time event loops.

## 6. Analytics and optimisation cost model

Predictive-maintenance preprocessing is linear in rows × features where possible. Dense all-pairs calculations are prohibited unless the declared size is small. Baseline models precede expensive search, and cross-validation folds × parameter candidates must fit the standard budget.

Allocation, marketing and portfolio problems may be combinatorial. Every solver receives a wall-time/iteration limit, deterministic seed where supported, acceptable optimality gap and incumbent-return policy. Results report `optimal`, `feasible`, `infeasible`, `timeout` or `error`; a timeout incumbent is not called optimal.

## 7. Integrated-scenario budget

The integrated runner executes modules sequentially by default to simplify provenance and cap peak memory. It assigns stable derived seeds and releases large intermediate objects after writing validated artefacts. The standard integrated budget is:

- validation and setup: 10 s;
- digital twin: 60 s;
- predictive maintenance: 30 s;
- resource allocation: 30 s;
- marketing optimisation: 20 s;
- R&D portfolio: 20 s;
- cross-checks, serialization and report data: 10 s.

The total target is 180 seconds with 2 GiB peak memory. Module budgets are ceilings, not reservations; unused time need not be redistributed automatically.

## 8. Stochastic experiment budget

Smoke tests use one fixed seed. A standard uncertainty comparison uses 10 seeds; a publishable synthetic study should justify at least 30 or show convergence. Before launching a campaign:

\[
\text{estimated cost} = \text{scenarios} \times \text{seeds} \times \text{measured baseline runtime}
\]

The runner displays this estimate and requires explicit opt-in above 30 minutes or 2 GiB of projected outputs. Early stopping is permitted only through a predeclared convergence rule and records skipped replications.

## 9. Storage and serialization budget

Generated artefacts do not belong in source control unless they are small reviewed fixtures. Each run has a manifest, compact KPI result and optional detailed tables. Recommended first-iteration limits are:

- manifest and configuration: ≤ 1 MiB;
- KPI/result summaries: ≤ 10 MiB;
- detailed event/observation tables: ≤ 200 MiB per integrated run;
- logs: ≤ 10 MiB, rotated or truncated with an explicit marker;
- retained standard runs: 20 per scenario family by default.

JSON is used for contracts and small records; CSV for simple interchange; Parquet is preferred for large tabular artefacts if the optional dependency is installed. Compression and downsampling never replace the immutable source hash.

## 10. Test and CI budget

The ordinary local/CI suite targets:

- unit tests: ≤ 60 seconds;
- contract and architecture tests: ≤ 30 seconds;
- integration smoke scenario: ≤ 60 seconds;
- total default suite: ≤ 3 minutes on the reference class.

Long stochastic, solver-benchmark and research tests are marked and run separately. Tests never depend on wall-clock sleeps, network services or unseeded randomness. Performance tests compare trends and generous ceilings to avoid hardware-noise failures.

## 11. Instrumentation

Every standard or larger run records wall time, process CPU time, peak resident memory, input row/entity counts, DES event count, solver iterations/status, artefact bytes and warning/limit events. Module timings are captured around public entry points with low-overhead standard tooling.

Benchmark reports compare like-for-like configurations and include median plus dispersion over repeated runs. Profiling artefacts are generated only on demand because they can be large and contain input-derived values.

## 12. Guardrails and failure behaviour

- Validate sizes before allocating large arrays or constructing optimisation matrices.
- Stream or chunk large tabular inputs and event outputs.
- Use integer/count and finite-number checks at boundaries.
- Apply event, iteration, recursion, rework, horizon and solver-time limits.
- Write artefacts to a temporary run directory, then finalize the manifest only after validation.
- On cancellation/limit, preserve a diagnostic manifest and remove no previous successful run.
- Never retry deterministic invalid input automatically.

Warnings at 80% of a limit help analysts resize scenarios before failure.

## 13. Parallelism policy

The first iteration defaults to sequential module execution and may parallelize independent seed replications with a small, explicit process count. Library code must not create unbounded pools or change global thread settings. Parallel runs receive separate derived seeds and output directories. The aggregate memory estimate, not CPU count alone, limits concurrency.

No GPU, cluster, queue, distributed database or service orchestration is required. Optional parallelism must produce statistically equivalent results to sequential execution within declared tolerances.

## 14. Scale-up triggers and acceptance criteria

Revisit the architecture only when representative, profiled workloads repeatedly exceed a guardrail after algorithmic and data-layout improvements, or when a validated use case requires isolation/concurrency unavailable locally. Candidate evidence includes more than 2 million DES events per required run, more than 4 GiB working memory, campaigns exceeding 30 minutes that cannot be reduced, or multiple governed users requiring concurrent execution.

The compute budget is accepted when every public runner enforces input and runtime limits, standard scenarios meet their target on the recorded reference environment, the full default test suite meets its budget, repeated seeded runs are reproducible, and limit failures produce contract-valid diagnostics without corrupting completed artefacts.
