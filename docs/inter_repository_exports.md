# SylvaPapers — Inter-repository exports

## 1. Purpose and ownership

This document is the stable file handoff from the SylvaPapers Module A/B repository to the future,
separate Module D marketing and Module E R&D repositories. Downstream code must depend on these
files and their metadata, never on `sylvapapers_digital_twin`, `sylvapapers_maintenance` or private
runtime objects.

The producer owns schemas, definitions and backwards-compatible generation. Each consumer owns a
strict ingress validator, an immutable raw-data landing area and any derived analytical tables.

## 2. Export bundles

| File | Grain | Required consumer | Main decision evidence |
|---|---|---|---|
| `campaign_runs.csv` | campaign × replication | D and E | all 21 KPI, counts, seed, horizon and runtime |
| `kpi_statistics.csv` | campaign × KPI | D and E | mean, dispersion, empirical quantiles and 95% mean CI |
| `module_d_product_statistics.csv` | campaign × replication × product | D | demand-servicing capacity, throughput, delay, rejects, recycling and final loss |
| `module_e_machine_statistics.csv` | campaign × replication × machine | E | load, failures, downtime, maintenance, energy, emissions and synthetic cost |
| `machine_decision_features.csv` | analysis × machine | D and E | failure risk, RUL, policy, downtime, cost and capacity impact |
| `maintenance_policy_costs.csv` | analysis × machine × policy | optional E | corrective, preventive and predictive economic alternatives |
| `machine_economic_priorities.csv` | model × machine | D and E | predicted lost revenue, rank and expected net benefit |
| `economic_model_feature_importance.csv` | model × feature | E | holdout permutation importance |

The campaign bundle also includes `campaign_metadata.json` and `column_dictionary.json`. The Module B
bundle includes `module_b_manifest.json`. These adjacent JSON files are mandatory control evidence
even when the receiving model reads only CSV.

The compact handoff adds `handoff_manifest.json`, which records every copied file, target consumers,
byte size, CSV row count and header, plus its SHA-256 digest.

## 3. Identity, provenance and versions

| Field or document | Rule |
|---|---|
| `schema_version` | semantic exchange version; current value `1.0.0` |
| `producer_version` | SylvaPapers generator version; current campaign value `0.5.0` |
| `data_classification` | current baseline is `synthetic_hypothesis_not_calibrated` |
| `provenance` | identifies the producing simulation, temporal backtest or decision-feature step |
| `campaign_id`, `scenario_id` | stable experiment identity; never infer these from filenames |
| `replication`, `seed` | stochastic sample identity for campaign tables |
| `source_schema_version`, `source_code_version` | Module B lineage back to its Module A bundle |
| `generated_at` | generation timestamp in the adjacent JSON metadata or manifest |
| `analysis_reference_at` | simulated timestamp at which the Module B assessment was made |

A consumer must preserve these fields unchanged in its raw layer. Synthetic values must never be
relabeled as observed or calibrated data. Module D/E outputs must retain the source campaign or
analysis identity so a decision can be traced back to one exact simulation bundle.

## 4. Units and statistical interpretation

| Domain | Canonical unit or interpretation |
|---|---|
| production quantity | `roll` or explicitly named `roll_equivalent` |
| throughput | `roll/hour` |
| simulated durations | `minute`; RUL uses `operating_hour`; warning lead uses `calendar_hour` |
| probabilities, rates and capacity impact | ratio in `[0, 1]`, never percentage points |
| energy | `kWh` |
| emissions | `kgCO2e`, synthetic estimate from configured factors |
| machine cost, revenue and failure loss | `EUR`, explicit synthetic hypotheses rather than accounting observations |
| Module B policy cost | currency declared per row and in `module_b_manifest.json` |
| 95% confidence interval | seeded non-parametric bootstrap percentile interval across replications |

`column_dictionary.json` is authoritative for campaign column types, units and descriptions. A 95%
confidence interval describes uncertainty of the simulated replication mean under one fixed factory
and scenario; it is not a plant-performance guarantee. The reference campaign contains 100
replications of 2,000 jobs with seeds 1000–1099.

## 5. Compatibility policy

| Change | Consumer action |
|---|---|
| same major version, added column | accept and ignore or map the unknown additive field |
| same major version, reordered columns | accept by header name, never by position |
| same major version, missing required column | reject the bundle with a clear validation error |
| changed unit, grain or field meaning | require a schema-version change and explicit migration |
| different major schema version | reject until the consumer implements a reviewed adapter |
| missing dictionary, manifest or provenance | reject; do not guess metadata |

CSV encoding is UTF-8 with one header row and scalar cells. Producers neutralize spreadsheet-formula
prefixes in text values, but consumers must still treat all copied files as untrusted input: bound
file and row sizes, parse strict numeric and datetime fields, reject duplicate logical keys and avoid
executing cell content.

## 6. Generation and copy procedure

Run the campaign first, then analyze the deliberately selected failure-bearing Module A sample. The
selected sample is useful for Module B validation but is not statistically representative.

```powershell
uv run sylvapapers campaign --config configs/campaigns/long_run.yaml --output outputs/long-run-statistics
uv run sylvapapers maintenance --input outputs/long-run-statistics/representative_module_a --output outputs/long-run-maintenance --config configs/maintenance/baseline.yaml
uv run sylvapapers economic-model --input outputs/long-run-statistics/module_e_machine_statistics.csv --output outputs/economic-model
uv run sylvapapers prepare-exchange --campaign outputs/long-run-statistics --maintenance outputs/long-run-maintenance --economic-model outputs/economic-model --output exports/sylvapapers-handoff-v2

$sylvaHandoff = Resolve-Path "exports/sylvapapers-handoff-v2"
$moduleDRepo = Resolve-Path "..\SylvaPapers-Module-D"
$moduleERepo = Resolve-Path "..\SylvaPapers-Module-E"

Copy-Item -LiteralPath "$sylvaHandoff\module_d_product_statistics.csv","$sylvaHandoff\kpi_statistics.csv","$sylvaHandoff\campaign_metadata.json","$sylvaHandoff\column_dictionary.json","$sylvaHandoff\machine_decision_features.csv","$sylvaHandoff\module_b_manifest.json","$sylvaHandoff\handoff_manifest.json" -Destination "$moduleDRepo\data\raw"
Copy-Item -LiteralPath "$sylvaHandoff\module_e_machine_statistics.csv","$sylvaHandoff\kpi_statistics.csv","$sylvaHandoff\campaign_metadata.json","$sylvaHandoff\column_dictionary.json","$sylvaHandoff\machine_decision_features.csv","$sylvaHandoff\maintenance_policy_costs.csv","$sylvaHandoff\temporal_validation_metrics.csv","$sylvaHandoff\probability_calibration.csv","$sylvaHandoff\module_b_manifest.json","$sylvaHandoff\handoff_manifest.json" -Destination "$moduleERepo\data\raw"
```

Create the destination `data/raw` directories in their own repositories before copying. Do not edit
raw files after transfer. Record the source Git commit and copy timestamp in each consumer's import
receipt; the producer metadata already records configuration digests and runtime environment.
The handoff command also verifies compatible schema majors, matching classifications, unique CSV
headers and records hashes; downstream validators must still verify the copied files independently.

## 7. Required consumer validation

1. Verify that every required file from the chosen bundle is present.
2. Read the adjacent dictionary or manifest before parsing business rows.
3. Accept only supported `schema_version` major versions, record `producer_version` and verify declared UTF-8 CSV compatibility.
4. Enforce required columns, units, value bounds, unique logical keys and referential identities.
5. Confirm all files agree on campaign or Module B source identity and data classification.
6. Persist an immutable raw copy and an import receipt before deriving features.
7. Separate synthetic hypotheses from any future observed or calibrated datasets.

Module D should join product statistics to KPI statistics by campaign/scenario/replication and use
machine decision features only as capacity-risk context. Module E should aggregate machine evidence
across replications before comparing R&D projects and must not treat a recommended maintenance
policy as an already executed intervention.

## 8. Current limitations

- Recycling is a Bernoulli recovery per `roll_equivalent`, with yield 0.75 and at most two loops; it
  is not a continuous fibre, moisture or broke balance.
- The campaign changes seeds only; factory topology and scenario assumptions are shared by all runs.
- The 95% confidence interval uses a seeded percentile bootstrap over 100 synthetic replications.
- Module B temporal windows overlap; right-censored windows are excluded from confusion and
  calibration, and small-event metrics remain descriptive.
- Costs, emissions, failures, sensors and economic parameters are synthetic and uncalibrated.
- Separate Module D and E repositories and their ingress validators are not created in this repository.
