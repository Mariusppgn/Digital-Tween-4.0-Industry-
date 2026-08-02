# SylvaPapers — Scientific methodology

## 1. Positioning

SylvaPapers is a reproducible software experiment, not a calibrated model of a specific paper mill.
Module A tests a synthetic production system; Module B tests interpretable maintenance methods on
its synthetic evidence.

## 2. Reproducibility

Every run declares schema version, provenance, configuration, seed, horizon and output path. Equal
validated Module A inputs and seed must reproduce equal events, states and sensors. Module B is
deterministic for an identical persisted bundle and maintenance configuration.

## 3. Module A process experiment

The graph represents serial transformations, alternative pulp recipes and redundant machines. A
product may declare a route or let the simulator derive it from edge conditions. Enabled routes
terminate in accepted rolls or measured losses. Queue and WIP histories expose accumulation, while a
continuous dry-tonne balance remains outside the baseline.

## 4. Module A reliability experiment

The common two-parameter Weibull family changes shape and scale by machine type. Failure probability
is conditioned on operating age and interval duration. Degradation, repair and maintenance recovery
are explicit synthetic engineering choices. Comparative experiments vary one factor at a time before
factorial or sensitivity designs.

## 5. Module A instrumentation

State-derived synthetic sensors cover load, temperature, vibration, pressure, power, operating age
and degradation. Each record has units and a quality label. A sensor series is evidence about the
simulator's latent state, not evidence that the same relationship exists in a real paper machine.

## 6. Module B anomaly experiment

EWMA weights recent observations while retaining historical context. Robust location and scale reduce
the influence of isolated extremes, and variable importance explains which channels drive the latest
score. Validation must use chronological baselines and avoid fitting thresholds on future failures.

## 7. Module B reliability and uncertainty

Conditional Weibull risk estimates failure probability between current operating age and the chosen
horizon. The RUL result is expressed in operating hours and includes an uncertainty interval. Useful
validation includes temporal discrimination, probability calibration and interval coverage; these
cannot be claimed from a tiny synthetic demonstration alone.

## 8. Maintenance policy experiment

Corrective, preventive and predictive policies are compared under one explicit synthetic economic
configuration. The comparison reports expected cost, downtime and intervention probability. It does
not optimize a real work schedule or prove savings.

## 9. KPI and visual evidence

Module A reports production, service, cycle time, utilization, defects, losses, downtime, cost,
energy, simplified OEE and delay. Module B reports anomaly, failure risk, RUL, recommendation and
policy economics. Figures must be regenerated from saved inputs and never substitute for contract or
numeric validation.

## 10. Validation hierarchy

1. validate contracts, units, references and provenance;
2. validate graph reachability, product activation and output completeness;
3. test deterministic Module A events, states, sensors and KPI bounds;
4. test Module B anomaly, risk, RUL and policy formulas against simple baselines;
5. test file round trips, malformed-input rejection and bilingual documentation parity;
6. benchmark `fast`, `standard` and `research` separately;
7. compare synthetic scenarios only after the previous levels pass;
8. require approved historical backtesting before any operational interpretation.

## 11. Advanced-method gate

CUSUM, Cox models, isolation forests, state-space models, conformal prediction and lightweight RUL
learners are candidates, not implemented baseline requirements. An extension must improve a declared
time-aware metric or economic decision, fit the compute budget, preserve interpretability evidence
and retain the simple baseline for comparison.

## 12. Calibration pathway

Operational use requires approved process histories, censored failure data, synchronized sensor and
maintenance records, quality labels, energy metering and material balances. Calibration must preserve
a separate synthetic baseline for regression testing and document dataset shift, missingness,
censoring, uncertainty and model-monitoring rules.
