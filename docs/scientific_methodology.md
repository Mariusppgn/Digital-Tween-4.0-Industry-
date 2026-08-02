# SylvaPapers — Scientific methodology

## 1. Positioning

SylvaPapers is a reproducible software experiment, not a calibrated model of a specific paper mill.
Results test implementation behavior and synthetic hypotheses only.

## 2. Reproducibility

Every simulation declares schema version, provenance, seed, time horizon, products and orders. Equal
validated inputs and equal seed must produce equal events and jobs.

## 3. Process experiment

The graph represents serial transformations, alternative pulp recipes and redundant machines. A
product may declare a route or let the simulator derive it from edge conditions. All enabled routes
must terminate in accepted rolls or measured losses.

## 4. Reliability experiment

The common Weibull family changes only shape and scale by machine type. Failure probability is
conditioned on current operating age and operation duration. Comparative experiments vary one
coefficient at a time before factorial exploration.

## 5. Quality and losses

Quality outcomes are seeded Bernoulli events in the lightweight model. Rejected rolls are terminal
losses. No result may count a rejected roll as accepted production.

## 6. KPI

Primary outputs include accepted quantity, service rate, cycle time, utilization, defect rate,
material-loss rate, downtime, cost, energy, simplified OEE and delay.

## 7. Validation hierarchy

1. validate contracts and references;
2. validate graph reachability and product activation;
3. test deterministic events and KPI bounds;
4. test editor round trips and security boundaries;
5. compare synthetic results only after the first four levels pass.

## 8. Calibration pathway

Operational use requires approved process histories, censored failure data, maintenance records,
quality labels, energy metering and material balances. Calibration must preserve a separate synthetic
baseline for regression testing.
