# SylvaPapers — Roadmap

## Status legend

- ✅ complete and validated
- 🟡 planned or partially implemented
- ⬜ not started

## Factory foundation

| Increment | Status | Acceptance evidence |
|---|---|---|
| Versioned contracts and schemas | ✅ | strict Pydantic validation and schema tests |
| Raw wood to paper-roll graph | ✅ | serial chain, three recipe branches and redundant machines |
| Explicit step inputs and outputs | ✅ | materials visible in configuration and editor |
| Three activatable products | ✅ | disabled-product order rejection |
| Two-parameter Weibull by machine type | ✅ | density and conditional failure tests |
| Operating-age failure simulation | ✅ | seeded failure event behavior |
| Terminal measured losses, no recycling | ✅ | material-loss events and KPI |
| Local drag-and-drop editor | ✅ | browser QA, keyboard access and editor tests |
| Validated explicit configuration write | ✅ | server validation, atomic replacement and CSP |
| Complete SylvaPapers name migration | ✅ | packages, CLI, docs, CI and reports |

## Next modelling depth

| Increment | Status | Goal |
|---|---|---|
| Continuous dry-tonne material balance | ⬜ | yields, moisture and mass conservation |
| Calendar enforcement | 🟡 | shifts, planned stops and maintenance windows |
| Mid-operation failures | ⬜ | interrupt/resume/restart policies |
| Physical state per parallel machine | 🟡 | independent age and event identity for every instance |
| Repair-time distributions | ⬜ | seeded stochastic repair models |
| Product-grade changeovers | 🟡 | grade compatibility and transition costs |

## Decision modules

| Increment | Status | Goal |
|---|---|---|
| Predictive maintenance | ⬜ | interpretable risk and intervention ranking |
| Resource allocation | ⬜ | feasible production and maintenance schedules |
| Scenario optimization | ⬜ | capacity, cost, energy and loss trade-offs |
| Data calibration workflow | ⬜ | fit synthetic parameters to approved plant evidence |

No future increment may be presented as operationally calibrated without approved industrial data.
