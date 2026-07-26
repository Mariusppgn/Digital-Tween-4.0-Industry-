# Scientific methodology

## 1. Objective and evidence level

Asteria Composites Lab is a reproducible experimental environment, not a calibrated representation of a specific factory. It studies how production flow, asset reliability, resource allocation, market choices and R&D portfolios interact under explicit synthetic assumptions. Results support software verification and hypothesis exploration only until comparison with approved industrial data.

Every output carries one evidence label:

- **synthetic:** generated entirely from documented assumptions;
- **calibrated:** selected parameters fitted on a traceable dataset;
- **validated:** evaluated on independent data against predeclared criteria.

The first iteration is **synthetic**.

## 2. Research questions and hypotheses

| Project | Research question | Testable first-iteration hypothesis |
|---|---|---|
| Digital twin | Where do queues and variability constrain throughput? | Autoclave batching, finite buffer capacity and rework produce measurable bottlenecks |
| Predictive maintenance | Can asset history prioritise interventions? | A seeded degradation/failure model ranks high-risk assets above healthy controls |
| Resource allocation | Can scarce people and machines be assigned feasibly? | A constrained allocation improves the declared objective over a simple baseline without violating capacity |
| Marketing optimisation | How should a bounded campaign budget be distributed? | Optimisation improves expected contribution over uniform allocation under the same assumptions |
| R&D portfolio | Which projects fit budget and strategic constraints? | Constrained selection outperforms a score-only greedy baseline on expected portfolio value |
| Integrated scenario | Are cross-domain recommendations coherent? | Contracted snapshots allow reproducible propagation of capacity and demand assumptions without package coupling |

Hypotheses, metrics and rejection criteria are frozen before running a comparison.

## 3. Common experimental protocol

1. Define a baseline, question, factor ranges, constraints and acceptance metrics.
2. Validate inputs through `asteria_contracts` and freeze a manifest.
3. Derive one independent random seed per module from a master seed.
4. Execute the baseline and alternatives with identical exogenous conditions.
5. Check domain invariants before calculating KPIs.
6. Repeat stochastic cases across a declared seed set.
7. Report effect size, dispersion, failed runs and limitations.
8. Preserve configuration, results, versions and hashes as immutable artefacts.

Changing the hypothesis, metric or exclusion rule after seeing results creates a new experiment.

## 4. Digital-twin method

### 4.1 Model type

The factory is a terminating discrete-event simulation. An event calendar advances simulated time to the next event; no wall-clock waiting is used. Entities traverse:

`MP → cut → one of two parallel layup stations → finite buffer → batched autoclave → finish → QC → pass, bounded rework, or scrap`.

Resources have capacity, calendars, setup and failure state. Processing times are non-negative seeded distributions. Queue discipline defaults to FIFO with deterministic tie-breaking. The autoclave starts according to declared batch capacity and release policy. Rework count has a hard limit.

### 4.2 Invariants and KPIs

For every completed run:

- entity conservation holds: released = in-process + finished + scrapped;
- event time is monotonic and no duration is negative;
- resource occupancy never exceeds capacity;
- an entity occupies at most one processing resource at a time;
- rework count and queue lengths remain within configured bounds.

Primary KPIs are throughput, lead time, work in progress, queue time by station, utilisation, autoclave fill rate, on-time completion, first-pass yield, rework and scrap rate. Warm-up and observation windows are declared whenever steady-state metrics are used.

## 5. Predictive-maintenance method

The synthetic asset dataset combines age, operating hours, load, temperature/vibration proxies, maintenance history and seeded failure labels. A transparent baseline—such as threshold rules or regularised classification—must precede any more complex model. Splits are chronological or asset-grouped to prevent observations from the same failure episode leaking across train and test.

Evaluation includes precision, recall, PR-AUC, calibration, lead time before failure, false alarms per operating period and maintenance capacity consumed. Class imbalance is reported. A risk score is not a remaining-useful-life guarantee and never triggers automatic equipment control.

## 6. Resource-allocation method

The allocation model declares resources, skills, availability, tasks, durations, priorities and compatibility constraints. Hard constraints cover capacity, non-overlap, eligibility and required coverage. The objective is a documented weighted combination such as lateness, utilisation imbalance, changeovers and unmet demand.

Every optimiser is compared with a deterministic baseline and returns feasibility status, objective components, binding constraints and unassigned work. If no feasible solution exists, the system reports a minimal diagnostic rather than silently relaxing constraints.

## 7. Marketing-optimisation method

Synthetic segments and channels carry budget bounds, expected response, unit margin, saturation and uncertainty. The experiment compares a uniform or historical-style baseline with a constrained allocation. Outcomes include expected contribution, acquisition volume, spend, marginal return and concentration by channel/segment.

Response functions are scenario assumptions, not causal estimates. No result is interpreted as market evidence without a controlled experiment or approved observational methodology. Sensitivity to response and margin assumptions is mandatory.

## 8. R&D-portfolio method

Each candidate project has cost, duration, expected value, success probability, strategic score, resource demand, dependencies and exclusions. Selection respects budget, capacity, prerequisite and diversification constraints. Outputs separate raw expected value from strategic weighting and list rejected projects with binding reasons.

The reference comparison is a transparent greedy or rank-based policy. Uncertain cost, value and success are propagated through scenarios; the model does not hide value judgements inside a single unexplained score.

## 9. Synthetic-data generation

Generation follows a causal order: scenario assumptions → latent entities/events → noisy observations → missingness/faults → derived features. Master and derived seeds are stored. Default distributions, ranges and correlations live in versioned configuration. Fault injection is opt-in and records target, onset, duration and magnitude.

Synthetic data must contain:

- stable identifiers and valid foreign-key relationships;
- explicit units, timestamps/simulated time and provenance;
- realistic class imbalance and bounded noise where relevant;
- edge cases for zero demand, full capacity, downtime, infeasibility and rework;
- a prominent `source = synthetic` marker.

Missing values remain missing in raw data. Imputation creates a derived dataset with method and version.

## 10. Verification and validation

Software verification precedes empirical validation:

- unit tests for deterministic calculations and boundary cases;
- property tests for conservation, bounds, monotonic time and feasibility;
- fixed-seed replay and stable result hashes where serialization permits;
- hand-computable micro-scenarios for each module;
- sensitivity tests showing expected directional response;
- integration tests validating all exchanged contracts;
- termination tests for queues, rework and optimisation time limits.

Validation uses data withheld by time, asset, batch or campaign, never adjacent-row random splits when leakage is possible. Metrics and thresholds are declared before evaluation. A plausible dashboard is not validation evidence.

## 11. Experimental design and uncertainty

One-factor-at-a-time scenarios explain local behaviour; factorial or Latin-hypercube designs explore interactions. Minimum integrated factors include demand, process-time variability, failure intensity, layup staffing, autoclave batch policy, QC defect probability, maintenance capacity, campaign budget and R&D budget.

Stochastic outputs are reported over multiple seeds using median, quantiles and confidence intervals where justified. Sensitivity ranks influential assumptions without claiming causality. Measurement, parameter, model-form and scenario uncertainty are distinguished. Failed runs are counted, not discarded without explanation.

## 12. Reproducibility and provenance

Each run records experiment ID, immutable canonical inputs, master/derived seeds, package and contract versions, code revision, dependency/runtime fingerprint, dataset hashes, start/end times, warnings, invariant results, output hashes and evidence label. Exported results include a machine-readable manifest and a human-readable limitations section.

Exact cross-platform floating-point identity is not promised. Comparisons use documented tolerances, feasibility equivalence and distributional invariants.

## 13. Limitations and promotion rules

The first iteration excludes detailed cure physics, spatial plant layout, human factors, supplier disruption, causal marketing inference, automated maintenance action and real-time factory control. Synthetic optima may exploit assumptions absent from reality. Promotion from **synthetic** to **calibrated**, then **validated**, requires governed source data, leakage review, independent evaluation, predefined gates and sign-off by the relevant industrial owner. Any material change to equations, constraints, distributions or KPI definitions triggers a new model version and validation-impact review.
