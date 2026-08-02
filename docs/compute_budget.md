# SylvaPapers — Compute budget

## 1. Objective

Keep factory editing, Module A simulation and Module B maintenance analysis practical on a standard
developer laptop without a GPU. These budgets are engineering guardrails, not measured service-level
agreements.

## 2. Profiles

| Profile | Intended workload | End-to-end guardrail |
|---|---|---:|
| `fast` | smoke scenario, tests and one maintenance pass | < 30 s per simple run |
| `standard` | one industrial month, several replications and policy comparison | < 2 min |
| `research` | optional sensitivity or advanced-method comparison | < 5 min per default configuration |

A named benchmark must record hardware, Python version, scenario, seed, repetitions, artefact counts
and wall-clock time before any guardrail is presented as an observed result.

## 3. Module budgets

| Activity | `fast` target | Scaling control |
|---|---:|---|
| Contract and graph validation | < 2 s | graph size and schema count |
| Editor initial load | < 3 s | nodes, edges and 2 MB save cap |
| Module A simple simulation | < 30 s | orders, horizon and optional figures |
| Module B baseline analysis | < 30 s | machines, samples, horizon and figures |
| Complete local test suite | < 60 s | excludes dependency installation |

## 4. Memory and output

Configurations stay human-readable. Tabular observations are compact rows, while figures and result
bundles are written outside source files. Module A and B outputs use separate directories so
maintenance analysis cannot overwrite its source evidence.

## 5. Algorithm policy

EWMA, robust thresholds and closed-form Weibull calculations are the default laptop baselines.
Optional CUSUM, survival, state-space or machine-learning methods must share the same input/output
contracts, expose their cost and remain disabled in `fast`.

## 6. Termination guards

Product routes must terminate at a sink. The factory has no recycling or rework cycle. Simulation
horizon, order count and output size are bounded by validated configuration; maintenance input must
be a finite, complete result bundle.

## 7. Measurement

Each experiment summary records Python version, platform, schema and code versions, seed, profile,
scenario, runtime, input paths, output paths and result counts.
