"""JSON Schema export helpers for API and data-lake consumers."""

from __future__ import annotations

import json
from pathlib import Path

from . import models
from .models import ContractModel


def contract_types() -> dict[str, type[ContractModel]]:
    """Return the stable registry of top-level public contracts."""

    names = (
        "FactoryConfig",
        "ProcessGraph",
        "MachineConfig",
        "ProductDefinition",
        "ProductionOrder",
        "DemandScenario",
        "SimulationScenario",
        "SimulationEvent",
        "MachineState",
        "SensorRecord",
        "FailureEvent",
        "MaintenanceRecommendation",
        "ResourceCalendar",
        "ProductionSchedule",
        "MarketingPlan",
        "DemandForecast",
        "RDProject",
        "RDPortfolio",
        "KPIReport",
    )
    return {name: getattr(models, name) for name in names}


def export_json_schemas(directory: str | Path) -> list[Path]:
    """Write one deterministic JSON Schema file per public contract."""

    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, contract in contract_types().items():
        target = destination / f"{name}.schema.json"
        target.write_text(
            json.dumps(contract.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.append(target)
    return written
