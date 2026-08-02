# SylvaPapers — Data contracts

## 1. Contract rules

`sylvapapers_contracts` uses strict Pydantic v2 models. Unknown fields are rejected, schema versions
use semantic-version strings, and provenance labels distinguish synthetic assumptions from evidence.

## 2. Factory contracts

| Contract | Purpose | Key validation |
|---|---|---|
| `FactoryConfig` | Factory identity, types, machines, graph and calendars | unique IDs and valid references |
| `MachineTypeConfig` | Shared equipment-type reliability | unique type and Weibull density |
| `FailureDensityConfig` | Two-parameter Weibull family | positive shape and scale hours |
| `MachineConfig` | Physical equipment capacity and metadata | positive capacity and declared type |
| `ProcessGraph` | Editable process topology | unique nodes and non-dangling edges |
| `ProcessNode` | Step, materials and editor position | operation references machines |
| `ProcessEdge` | Directed material relation | valid source/target and bounded probability |

## 3. Scenario contracts

| Contract | Purpose | Key validation |
|---|---|---|
| `ProductDefinition` | Enabled state, recipe, timings and bill of materials | positive values; routing may be derived |
| `ProductionOrder` | Dated roll demand | positive quantity and due date after release |
| `SimulationScenario` | Products, orders, seed and horizon | known enabled products only |

## 4. Operational contracts

Events, machine states, sensor records, failure events, maintenance recommendations, schedules and KPI
reports remain public versioned contracts for later modules.

## 5. Editor interoperability

The editor imports and exports the JSON representation of `FactoryConfig`. Coordinates are stored in
`ProcessNode.position`; inputs and outputs are stored as material identifier lists. Server writes are
accepted only after full contract validation.

## 6. Schema generation

```bash
uv run python -c "from sylvapapers_contracts import export_json_schemas; export_json_schemas('schemas')"
```

Generated schemas are deterministic review artefacts and must be refreshed after contract changes.
