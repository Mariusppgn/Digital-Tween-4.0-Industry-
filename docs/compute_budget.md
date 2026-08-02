# SylvaPapers — Compute budget

## 1. Objective

Keep factory editing, validation and fast simulation practical on a developer laptop. These budgets
are engineering guardrails, not production service-level agreements.

## 2. Fast profile

| Activity | Budget |
|---|---:|
| Contract and graph validation | < 2 s |
| Ten-roll simulation without plots | < 30 s |
| Editor initial load | < 3 s |
| Complete local test suite | < 30 s |

## 3. Memory and output

The baseline configuration stays human-readable. Events are compact rows; generated plots and result
bundles are written outside source files. The browser editor caps save payloads at 2 MB.

## 4. Termination guards

Product routes must terminate at a sink. The SylvaPapers model has no recycling or rework cycle;
quality rejects leave the process as measured losses.

## 5. Measurement

Record Python version, platform, seed, scenario, runtime and result counts in each simulation summary.
