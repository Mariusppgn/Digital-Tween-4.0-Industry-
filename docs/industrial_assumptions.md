# Industrial assumptions

## 1. Status and intended use

This register defines the synthetic industrial world used by the first Asteria iteration. Values are plausible placeholders for software demonstrations, not measurements from an identified composites plant. They must be replaced or calibrated before operational use. Every experiment records the assumption-set version and any override.

Assumption confidence is:

- **A — confirmed:** supported by an approved source;
- **B — provisional:** plausible and awaiting confirmation;
- **C — synthetic:** invented to exercise behaviour.

Unless explicitly upgraded, all first-iteration values are **C — synthetic**.

## 2. Facility and operating calendar

The model represents one composites production value stream with raw-material preparation, cutting, two parallel layup stations, a finite pre-autoclave buffer, one autoclave, finishing, quality control and rework. It is a logical flow model, not a spatial layout.

The baseline calendar is five days per week, two 8-hour shifts per day. Planned breaks and preventive-maintenance windows reduce availability. Release stops outside the calendar; work already in an uninterrupted autoclave cycle may finish. Overtime is disabled unless a scenario enables and costs it.

## 3. Products, demand and routing

The baseline uses two synthetic product families: `PANEL_STD` and `PANEL_COMPLEX`. Both follow the same main route; `PANEL_COMPLEX` has longer layup/finish time and higher defect probability. Demand is represented as dated manufacturing orders or a seeded arrival process. Priority classes are normal and expedite; FIFO is the default within a class.

No entity may skip QC. A recoverable defect returns to finishing, then QC. Each part allows at most two rework loops; the next failure becomes scrap. Product mixing inside an autoclave batch is allowed only when recipe-family compatibility is declared.

## 4. Baseline station assumptions

| Stage | Capacity | Baseline processing assumption | Important rule |
|---|---:|---|---|
| MP | 1 | Triangular 20/30/45 min per kit | Material is available before cutting |
| Cut | 1 | Triangular 25/40/60 min per kit | One kit per cutter |
| Layup A | 1 | Lognormal-like positive duration, median 180 min standard | Eligible for both families |
| Layup B | 1 | Same baseline distribution with independent draws | Eligible for both families |
| Buffer | 6 parts | No processing time | Blocking applies when full |
| Autoclave | 1 batch resource, up to 4 compatible parts | Fixed 360 min plus 30 min load/unload | Starts full or after max wait of 120 min |
| Finish | 2 | Triangular 45/70/110 min per part | Rework consumes the same capacity |
| QC | 1 | Triangular 20/30/50 min per part | Routes to pass, rework or scrap |

These figures are scenario defaults, not accepted takt times. Durations are sampled once per activity from a named seeded distribution and cannot be negative. Setup/changeover effects are zero in the simplest baseline and explicit in advanced scenarios.

## 5. Quality and rework assumptions

Baseline first-pass defect probability is 6% for `PANEL_STD` and 10% for `PANEL_COMPLEX`. Conditional on a defect, 80% are assumed recoverable and 20% scrap. A first rework multiplies finishing time by 0.6; a second by 0.8. QC outcomes are independent in the simplest model except for the product family and rework count.

This independence is a known simplification. Future calibration should condition quality on material batch, operator/team, equipment state, waiting time, recipe compatibility and prior rework. Yield and scrap claims remain synthetic until this is done.

## 6. Reliability and maintenance assumptions

Cutting, layup, autoclave and finishing assets can fail. The baseline samples time to failure and repair from positive seeded distributions; planned maintenance restores the declared virtual age fraction. Failures pause or delay processing according to an explicit station policy. Autoclave interruption defaults to batch failure requiring QC review; this conservative rule is configurable.

Synthetic predictive-maintenance features are correlated with a latent degradation state. Sensor values, failure labels and maintenance actions are generated in causal order. No score is treated as a physical remaining-useful-life measurement. Maintenance technicians and maintenance windows are finite resources in allocation scenarios.

## 7. Workforce and resource-allocation assumptions

Workers have named skills such as material preparation, cutting, layup, autoclave operation, finishing, quality inspection and maintenance. A worker cannot cover overlapping tasks and is available only during assigned shifts. The baseline treats proficiency within a skill as equal and omits fatigue, ergonomics and learning curves.

Hard constraints include skill eligibility, availability, task coverage, station capacity and legal maximum hours declared by the scenario. Preference, fairness and overtime are soft objectives only when quantified. The optimiser may leave work unassigned rather than fabricate capacity.

## 8. Commercial and marketing assumptions

Marketing scenarios are separated from observed plant demand. They use synthetic segments, channels, response curves, unit margins, minimum/maximum spend and a single declared currency. Response exhibits diminishing returns and may be capped by feasible production capacity from the resource-allocation scenario.

No channel response is causal evidence. Campaign effects are expected scenario values and do not automatically create factory orders. An integrated experiment applies an explicit mapping and reports demand above feasible capacity as unmet or deferred, never as delivered revenue.

## 9. R&D-portfolio assumptions

Candidate projects are synthetic and carry cost, duration, success probability, expected value, strategic scores, dependencies, exclusions and resource demand. Costs and capacity share one planning horizon. Expected value is risk-adjusted only when the formula is declared; strategic weights remain visible.

Portfolio selection cannot prove innovation value. It produces a constrained, explainable scenario under stated inputs. Mandatory projects, diversification floors and prerequisites are hard constraints; subjective scores require an owner and review date.

## 10. Data and integration assumptions

The first iteration reads versioned local YAML/JSON/CSV/Parquet artefacts and runs offline in one Python process per experiment. It assumes no live MES, ERP, historian, OPC UA, MQTT, cloud database or distributed scheduler. Absolute timestamps use UTC; DES uses non-negative simulated minutes.

Synthetic identifiers contain no personal or confidential plant data. Raw inputs are immutable, derived artefacts carry source hashes, and missing values are not silently filled. Cross-module exchange occurs only through `asteria_contracts`.

## 11. Safety, security and decision boundaries

Asteria has no actuator interface and cannot control equipment, release parts, schedule real workers, trigger maintenance, spend marketing budget or approve R&D investment. Outputs are advisory experiment artefacts. Production use would require authentication, authorization, audit, network segmentation, data classification, retention rules, hazard analysis and human approval.

No generated dataset should include real personal data or confidential operational details without an approved governance process. Logs and validation errors must avoid payload dumps.

## 12. Assumption-change protocol

Every assumption has an ID, owner, value/range, unit, confidence, source, validity period and affected modules. A change:

1. creates a new assumption-set version;
2. identifies affected contracts, fixtures and baselines;
3. reruns verification and sensitivity cases;
4. records KPI deltas and migration notes;
5. requires domain review before upgrading confidence.

Changing a baseline never overwrites previous experiment manifests.

## 13. Industrial calibration backlog

Before any calibrated claim, obtain and govern:

- actual routing, calendars, capacities, buffer rules and autoclave batch policy;
- product-family processing-time distributions and changeovers;
- order arrivals, due dates and priority rules;
- failure, repair, preventive-maintenance and sensor histories;
- quality, rework and scrap definitions linked to traceable causes;
- workforce skills/availability with privacy protection;
- commercial response evidence and production-capacity linkage;
- R&D costs, resource constraints, scoring governance and outcome history.

Calibration must separate estimation data from independent validation periods and document known selection bias.

## 14. Acceptance criteria

The assumption register is adequate for the first iteration when every scenario value is traceable to a versioned entry, all defaults are visibly synthetic, ranges prevent impossible states, integrated mappings declare their limitations, and sensitivity tests show which conclusions change when high-impact assumptions vary. No report may omit the evidence label or imply factory validation.
