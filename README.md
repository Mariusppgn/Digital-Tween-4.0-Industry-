# SylvaPapers

> A modular and reproducible paper-mill digital twin, from raw wood to maintenance decisions.

[English](README.md) · [Français](README_FR.md) · [Architecture EN](docs/architecture.md) · [Architecture FR](docs/architecture_FR.md) · [Modules A/B EN](docs/modules_a_b.md) · [Modules A/B FR](docs/modules_a_b_FR.md) · [Roadmap](ROADMAP.md) · [License](LICENSE)

## Summary

SylvaPapers models a fictional integrated paper mill. Module A simulates the configurable factory and
generates auditable operational, reliability and sensor data. Module B consumes those public outputs
to produce interpretable anomaly, failure-risk, remaining-life and maintenance-policy results.

All industrial values shipped in this repository are **synthetic engineering assumptions**. They are
not calibrated measurements and must not be used for real operational decisions.

## Ecosystem status

| Module | Business problem | Status in this increment |
|---|---|---|
| A — Digital twin | Simulate production, reliability, quality, energy and cost | Implemented baseline |
| B — Predictive maintenance | Detect drift, estimate failure risk and compare policies | Implemented interpretable baseline |
| C — Resource allocation | Schedule production, people and maintenance | Contracts and A/B inputs prepared |
| D — Marketing optimization | Convert capacity-aware demand into budget decisions | Contracts prepared; model not implemented |
| E — R&D portfolio | Select improvements under cost, resource and risk constraints | Contracts prepared; model not implemented |

```mermaid
flowchart LR
    Demand[Demand and orders] --> A[Module A: digital twin]
    A -->|states, sensors, failures| B[Module B: maintenance]
    B -->|recommendations and windows| C[Module C: allocation]
    C -->|schedule policy| A
    A -->|capacity, losses, costs| D[Module D: marketing]
    A -->|bottlenecks and risks| E[Module E: R&D]
    D -->|market value| E
    E -->|future factory parameters| A
```

## Factory workflow

The reference process combines serial operations, redundant machines and three recipe branches:

```mermaid
flowchart LR
    WOOD[Raw wood] --> DEB[Parallel debarking]
    DEB --> CHIP[Parallel chipping]
    CHIP --> BUF[Chip silo]
    BUF -->|kraft| KRAFT[Kraft cooking]
    BUF -->|printing| TMP[Thermomechanical pulp]
    BUF -->|board| BOARD[Board-pulp cooking]
    KRAFT --> WASH[Pulp washing]
    TMP --> WASH
    BOARD --> WASH
    WASH --> SCREEN[Screening]
    SCREEN --> BLEACH[Optional parallel bleaching]
    SCREEN --> STOCK[Stock preparation]
    BLEACH --> STOCK
    STOCK --> REFINE[Final refining]
    REFINE --> FORM[Sheet forming]
    FORM --> PRESS[Pressing]
    PRESS --> DRY[Parallel drying]
    DRY --> CAL[Calendering]
    CAL --> WIND[Parallel winding]
    WIND --> QC{Quality control}
    QC -->|accepted| ROLLS[Paper rolls]
    QC -->|rejected| LOSS[Measured losses]
```

No recycling or rework loop is present. Rejected rolls are recorded as material losses.

## Module A — digital twin

The seeded discrete-event simulation covers three activatable paper products, conditional routes,
parallel equipment, machine operating age, two-parameter Weibull failures, repair and maintenance,
terminal quality losses, energy and cost. The current lightweight model tracks roll entities rather
than a continuous dry-tonne balance.

Its result bundle includes events, jobs, KPI and figures plus machine states, sensor records, failure
events, maintenance interventions, queue history, work in progress and final system state. Synthetic
sensors expose load, temperature, vibration, pressure, power, operating age and degradation.

## Module B — predictive maintenance

The first maintenance baseline deliberately favors fast, interpretable methods:

- EWMA and robust thresholds for multivariate sensor drift;
- conditional Weibull risk from operating age and a configurable prediction horizon;
- lightweight remaining useful life with an uncertainty interval;
- explicit alerts and maintenance recommendations with traceable reasons;
- economic comparison of corrective, preventive and predictive policies.

These results are decision support only. They are evaluated against synthetic failures and synthetic
cost assumptions; no claimed accuracy transfers to a real mill without calibration.

## Module A to B contract

| Module A artefact | Main content | Module B use |
|---|---|---|
| `machine_states.csv` | status, utilization and active order by machine | operating context |
| `sensors.csv` | timestamped values, units and quality | EWMA anomaly evidence |
| `failures.csv` | failure mode, severity and downtime | outcome and policy evaluation |
| `maintenance.csv` | intervention type, timing and effect | maintenance history |
| `events.csv` | production and reliability event journal | traceability and alignment |
| `summary.json` | seed, versions, runtime and counts | reproducibility checks |

Module B imports only versioned contracts and persisted result files. It does not import simulator
internals, so both modules can be extracted into separate packages later.

## Visual factory editor

Run [Lancer_SylvaPapers.bat](Lancer_SylvaPapers.bat) on Windows, or:

```bash
uv run sylvapapers factory-editor --factory configs/factory.yaml --port 8766
```

Then open `http://127.0.0.1:8766/`. The editor supports drag-and-drop and keyboard movement; add,
edit, duplicate and delete actions; material relations and explicit inputs/outputs; Weibull editing;
undo/redo; automatic layout; JSON import/export; validation; and explicit atomic writing.

## Installation

Prerequisites: Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev
```

## Quick start

```bash
uv run sylvapapers validate-config --config configs/scenarios/baseline.yaml
uv run sylvapapers simulate --config configs/scenarios/baseline.yaml --output outputs/baseline
uv run sylvapapers maintenance --input outputs/baseline --output outputs/maintenance
uv run sylvapapers report --input outputs/baseline --output reports/generated
```

Use the optional maintenance configuration when comparing non-default thresholds, costs or horizons:

```bash
uv run sylvapapers maintenance --input outputs/baseline --output outputs/maintenance --config configs/maintenance/baseline.yaml
```

## Compute profiles

| Profile | Intended use | Default budget |
|---|---|---:|
| `fast` | tests, smoke runs and demonstrations | < 30 s per simple run |
| `standard` | main analysis and policy comparison | < 2 min for a multi-replication month |
| `research` | optional sensitivity and deeper experiments | < 5 min per default configuration |

These are laptop engineering guardrails, not production service-level agreements. Heavy methods stay
optional behind the same contracts.

## Repository map

```text
configs/                     # Factory, simulation and maintenance configurations
data/examples/               # Synthetic products and orders
docs/                        # Architecture, contracts, methods and assumptions (EN/FR)
schemas/                     # Generated JSON Schemas
src/sylvapapers_contracts/   # Versioned Pydantic contracts
src/sylvapapers_digital_twin/# Module A, reporting and web editor
src/sylvapapers_maintenance/ # Module B maintenance analysis
tests/                       # Contracts, engines, editor and documentation parity
reports/                     # Delivery and generated experiment reports
```

## Validation

```bash
uv run ruff check .
uv run mypy
uv run pytest
```

The suite covers contracts, graph branches, active products, Weibull behavior, deterministic
simulation, instrumentation, measured losses, maintenance baselines, editor boundaries, JSON
interoperability and bilingual documentation structure.

## Scope and limits

- The factory is event-based and roll-based; continuous fibre, moisture and fluid physics are out of scope.
- Weibull, sensor, degradation, maintenance-cost and process coefficients are synthetic and uncalibrated.
- EWMA is a drift baseline, not a diagnosis; Weibull risk depends on its modelling assumptions.
- Calendar contracts exist, but full workforce and maintenance-window enforcement remains future work.
- Modules C–E have prepared boundaries and contracts, but no optimizer is claimed as implemented.
- SylvaPapers has no actuator or production-control interface and requires human review.

## License

Distributed under the [MIT License](LICENSE).
