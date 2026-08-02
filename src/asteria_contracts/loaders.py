"""Safe YAML/JSON loaders for versioned SylvaPapers contracts."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import BaseModel

from .models import FactoryConfig, SimulationScenario


def load_model[ModelT: BaseModel](
    path: str | Path,
    model_type: type[ModelT],
) -> ModelT:
    """Load a UTF-8 JSON or YAML document and validate it as ``model_type``."""

    source = Path(path)
    suffix = source.suffix.lower()
    with source.open(encoding="utf-8") as stream:
        if suffix == ".json":
            payload = json.load(stream)
        elif suffix in {".yaml", ".yml"}:
            payload = yaml.safe_load(stream)
        else:
            raise ValueError(f"unsupported contract format: {suffix or '<none>'}")
    return model_type.model_validate(payload)


def load_factory_config(path: str | Path) -> FactoryConfig:
    return load_model(path, FactoryConfig)


def load_simulation_scenario(path: str | Path) -> SimulationScenario:
    return load_model(path, SimulationScenario)
