# SylvaPapers — Industrial assumptions

## 1. Evidence status

Every baseline value is a synthetic engineering hypothesis. No value comes from a named mill,
maintenance system, historian or laboratory campaign. Calibration is required before operational use.

## 2. Process boundary

The integrated model starts with raw wood and ends with accepted finished paper rolls or measured
quality losses. It covers debarking, chipping, pulp production, washing, screening, optional
bleaching, stock preparation, refining, forming, pressing, drying, calendering, winding and QC.

## 3. Products

| Product | Initial state | Recipe branch | Nominal unit |
|---|---|---|---|
| Kraft paper roll | enabled | kraft cooking | roll |
| Printing paper roll | enabled | thermomechanical pulp | roll |
| Board paper roll | disabled | board-pulp cooking | roll |

Activation is explicit. An order for a disabled product is invalid.

## 4. Materials and losses

Each process node lists plain-language input and output materials. The lightweight simulator follows
roll entities rather than continuous mass balances. QC rejects are losses and leave the process;
recycling, rework and internal broke recovery are deliberately excluded. This is a modelling
boundary, not a description of recommended mill practice.

## 5. Machines and capacity

Parallel machine lists represent redundant alternatives serving one operation. Conditional branches
represent different product recipes. Processing times, capacities, energy and cost values are
synthetic and use the units declared in configuration.

## 6. Failure density

All machine types use a two-parameter Weibull model:

| Parameter | Meaning | Unit |
|---|---|---|
| `shape` β | failure-rate profile | dimensionless |
| `scale_hours` η | characteristic operating age | operating hours |

Machine age advances during processing. Conditional risk assumes that configured shape and scale
remain applicable over the prediction horizon. Maintenance applies partial virtual-age recovery.
Repair duration remains a synthetic parameter.

## 7. Degradation and sensors

The degradation index is a synthetic latent state driven by machine use and maintenance. Load,
temperature, vibration, pressure and power records are generated as interpretable correlates of that
state and operating context. Noise, coefficients and sampling do not represent a specific sensor,
machine vendor or measurement campaign.

`operating_age_hours` and `degradation_index` are model state channels, not independent physical
measurements. Sensor quality labels describe generated-record quality, not certified metrology.

## 8. Predictive-maintenance baseline

EWMA detects persistent shifts and robust scaling reduces sensitivity to isolated extremes. The
conditional Weibull model estimates horizon risk and remaining operating life. Both rely on a
representative baseline and correct time alignment; neither proves a failure cause.

Recommendation urgency combines synthetic anomaly, risk and criticality evidence. It is advisory and
must not create an automatic maintenance work order.

## 9. Maintenance economics

Corrective, preventive and predictive policies are compared using intervention cost, downtime cost,
planned and corrective duration, predictive effectiveness and age recovery. The baseline values in
`configs/maintenance/baseline.yaml` are marked synthetic. Expected costs support software comparison
only and are not financial forecasts.

## 10. Quality and calendars

Quality probability is synthetic. A rejected roll creates quality and material-loss events and is not
accepted production. Shift calendars are contractual data, but full workforce, planned-stop and
maintenance-window enforcement remains future work.

## 11. Safety boundary

SylvaPapers has no actuator interface and cannot control real equipment. Production deployment would
require approved data governance, identity, authorization, audit, network segmentation, hazard
analysis, model monitoring and human approval.

## 12. Calibration checklist

- confirm the real process topology, grades, capacities and material units;
- replace synthetic process, quality, energy, degradation and cost values;
- estimate Weibull coefficients from censored operating-hour histories;
- align sensors, machine states, failures and maintenance timestamps;
- backtest anomaly and risk decisions using time-aware splits;
- validate RUL coverage, probability calibration and maintenance economics;
- reconcile roll counts with dry-tonne and moisture balances;
- define approved loss, failure-mode and intervention taxonomies.
