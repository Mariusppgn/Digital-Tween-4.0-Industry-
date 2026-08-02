# SylvaPapers — Industrial assumptions

## 1. Evidence status

Every baseline value is a synthetic engineering hypothesis. No value comes from a named mill,
maintenance system or laboratory campaign. Calibration is required before operational use.

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
roll entities rather than continuous mass balances. QC rejects are counted as losses and leave the
process; recycling, rework and internal broke recovery are deliberately excluded.

## 5. Machines and capacity

Parallel machine lists represent redundant alternatives serving the same operation. Conditional
graph branches represent different product recipes. Processing times, capacities, energy and cost
values are synthetic and use the units declared in the configuration.

## 6. Failure density

All machine types use a two-parameter Weibull model:

| Parameter | Meaning | Unit |
|---|---|---|
| `shape` β | failure-rate profile | dimensionless |
| `scale_hours` η | characteristic operating age | operating hours |

Machine age advances only during processing. Maintenance applies the configured partial virtual-age
recovery. Repair time remains a deterministic synthetic machine parameter in this increment.

## 7. Quality

QC probability is synthetic. A rejected roll creates `qc_fail` and `material_loss` events and is not
included in accepted production. `material_loss_rate` reports lost rolls divided by released rolls.

## 8. Calendars

Shift calendars are contract data for production and maintenance teams. The current lightweight
simulator does not enforce them; this limitation is explicit in result interpretation.

## 9. Safety boundary

SylvaPapers has no actuator interface and cannot control real equipment. Production deployment would
require identity, authorization, audit, network segmentation, hazard analysis and human approval.

## 10. Calibration checklist

- confirm the real process topology and enabled grades;
- replace synthetic processing, capacity, yield, energy and cost values;
- estimate Weibull coefficients from censored operating-hour histories;
- validate repair and maintenance-recovery assumptions;
- reconcile roll counts with dry-tonne material balances;
- define approved loss and quality taxonomies.
