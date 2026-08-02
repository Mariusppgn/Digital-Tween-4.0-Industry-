"""Input adapters for direct contracts and tabular Module A exports."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, cast

import yaml

from sylvapapers_contracts import (
    FailureEvent,
    MachineState,
    MachineStatus,
    MaintenanceAnalysisConfig,
    MaintenanceIntervention,
    SensorRecord,
)

SENSOR_UNITS = {
    "load_ratio": "ratio",
    "temperature_c": "degC",
    "vibration_mm_s": "mm/s",
    "pressure_bar": "bar",
    "power_kw": "kW",
    "operating_age_hours": "h",
    "degradation_index": "ratio",
    "failure_probability": "ratio",
}


@dataclass(frozen=True)
class MaintenanceDataset:
    """Validated Module A data required by the maintenance baseline."""

    sensor_records: list[SensorRecord] = field(default_factory=list)
    machine_states: list[MachineState] = field(default_factory=list)
    failure_events: list[FailureEvent] = field(default_factory=list)
    maintenance_interventions: list[MaintenanceIntervention] = field(default_factory=list)
    provenance: str = "module_a"


def load_maintenance_config(path: str | Path | None = None) -> MaintenanceAnalysisConfig:
    """Load a strict maintenance YAML/JSON configuration or use safe defaults."""

    if path is None:
        return MaintenanceAnalysisConfig(provenance="synthetic_example")
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"maintenance configuration not found: {source}")
    try:
        raw: Any
        if source.suffix.lower() == ".json":
            raw = json.loads(source.read_text(encoding="utf-8"))
        else:
            raw = yaml.safe_load(source.read_text(encoding="utf-8"))
        return MaintenanceAnalysisConfig.model_validate(raw)
    except (json.JSONDecodeError, yaml.YAMLError, ValueError) as exc:
        raise ValueError(f"invalid maintenance configuration {source}: {exc}") from exc


def _finite_float(value: Any, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number, got {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _find(directory: Path, *names: str) -> Path | None:
    return next((directory / name for name in names if (directory / name).is_file()), None)


def _simulation_origin(directory: Path) -> datetime:
    summary_path = directory / "summary.json"
    if summary_path.is_file():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            candidates = (
                summary.get("simulation_start_at"),
                (summary.get("metadata") or {}).get("start_at"),
            )
            for value in candidates:
                if value:
                    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return datetime(1970, 1, 1, tzinfo=UTC)


def _timestamp(row: dict[str, str], origin: datetime) -> datetime:
    if value := row.get("timestamp"):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return origin + timedelta(minutes=_finite_float(row.get("time_minutes", 0), "time_minutes"))


def _load_sensor_records(directory: Path, origin: datetime) -> list[SensorRecord]:
    path = _find(directory, "sensors.csv", "sensor_records.csv")
    if path is None:
        return []
    records: list[SensorRecord] = []
    for index, row in enumerate(_read_rows(path), 1):
        values = {
            name: _finite_float(row[name], name)
            for name in SENSOR_UNITS
            if row.get(name) not in (None, "")
        }
        if not values:
            continue
        machine_id = str(row.get("machine_id") or "").strip()
        if not machine_id:
            raise ValueError(f"{path.name} row {index} has no machine_id")
        records.append(
            SensorRecord(
                sensor_id=str(row.get("sensor_id") or f"{machine_id}-synthetic"),
                machine_id=machine_id,
                timestamp=_timestamp(row, origin),
                values=values,
                units={name: SENSOR_UNITS[name] for name in values},
                quality=cast(
                    Literal["good", "uncertain", "bad"],
                    str(row.get("quality") or "good"),
                ),
                provenance="module_a",
            )
        )
    return records


def _load_machine_states(directory: Path, origin: datetime) -> list[MachineState]:
    path = _find(directory, "machine_states.csv", "states.csv")
    if path is None:
        return []
    records: list[MachineState] = []
    for index, row in enumerate(_read_rows(path), 1):
        machine_id = str(row.get("machine_id") or "").strip()
        if not machine_id:
            raise ValueError(f"{path.name} row {index} has no machine_id")
        remaining = row.get("remaining_minutes")
        operating_age = row.get("operating_age_hours")
        records.append(
            MachineState(
                machine_id=machine_id,
                timestamp=_timestamp(row, origin),
                status=MachineStatus(str(row.get("status") or "idle").lower()),
                active_order_id=(row.get("active_order_id") or row.get("job_id") or None),
                utilisation=_finite_float(row.get("utilisation") or 0, "utilisation"),
                remaining_minutes=(
                    _finite_float(remaining, "remaining_minutes") if remaining else None
                ),
                operating_age_hours=(
                    _finite_float(operating_age, "operating_age_hours") if operating_age else None
                ),
                provenance="module_a",
            )
        )
    return records


def _load_failure_events(directory: Path, origin: datetime) -> list[FailureEvent]:
    path = _find(directory, "failures.csv", "failure_events.csv")
    if path is None:
        return []
    records: list[FailureEvent] = []
    for index, row in enumerate(_read_rows(path), 1):
        machine_id = str(row.get("machine_id") or "").strip()
        if not machine_id:
            raise ValueError(f"{path.name} row {index} has no machine_id")
        records.append(
            FailureEvent(
                failure_id=str(row.get("failure_id") or f"failure-{index:06d}"),
                machine_id=machine_id,
                occurred_at=_timestamp(row, origin),
                failure_mode=str(row.get("failure_mode") or "unknown"),
                severity=int(_finite_float(row.get("severity") or 1, "severity")),
                downtime_minutes=_finite_float(
                    row.get("downtime_minutes") or 0, "downtime_minutes"
                ),
                provenance="module_a",
            )
        )
    return records


def _load_maintenance_interventions(
    directory: Path, origin: datetime
) -> list[MaintenanceIntervention]:
    path = _find(directory, "maintenance.csv", "maintenance_interventions.csv")
    if path is None:
        return []
    records: list[MaintenanceIntervention] = []
    for index, row in enumerate(_read_rows(path), 1):
        machine_id = str(row.get("machine_id") or "").strip()
        if not machine_id:
            raise ValueError(f"{path.name} row {index} has no machine_id")
        started_at = _timestamp(row, origin)
        if row.get("completed_at"):
            completed_at = datetime.fromisoformat(row["completed_at"].replace("Z", "+00:00"))
            if completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=UTC)
        else:
            completed_at = origin + timedelta(
                minutes=_finite_float(
                    row.get("completed_at_minutes") or row.get("time_minutes") or 0,
                    "completed_at_minutes",
                )
            )
        maintenance_type = cast(
            Literal["corrective", "preventive", "predictive"],
            str(row.get("maintenance_type") or "corrective"),
        )
        records.append(
            MaintenanceIntervention(
                intervention_id=str(row.get("intervention_id") or f"maintenance-{index:06d}"),
                machine_id=machine_id,
                maintenance_type=maintenance_type,
                started_at=started_at,
                completed_at=completed_at,
                duration_minutes=_finite_float(
                    row.get("duration_minutes") or 0, "duration_minutes"
                ),
                age_before_hours=_finite_float(
                    row.get("age_before_hours") or 0, "age_before_hours"
                ),
                age_after_hours=_finite_float(row.get("age_after_hours") or 0, "age_after_hours"),
                recovery_fraction=_finite_float(
                    row.get("recovery_fraction") or 0, "recovery_fraction"
                ),
                technician_resource=str(row.get("technician_resource") or "maintenance-team"),
                synthetic=str(row.get("synthetic") or "true").lower() == "true",
                provenance="module_a",
            )
        )
    return records


def load_module_a_outputs(directory: str | Path) -> MaintenanceDataset:
    """Load and validate the tabular output bundle produced by Module A."""

    source = Path(directory)
    if not source.is_dir():
        raise FileNotFoundError(f"Module A output directory not found: {source}")
    origin = _simulation_origin(source)
    sensors = _load_sensor_records(source, origin)
    if not sensors:
        raise ValueError(
            f"no sensor data found in {source}; expected sensors.csv or sensor_records.csv"
        )
    return MaintenanceDataset(
        sensor_records=sensors,
        machine_states=_load_machine_states(source, origin),
        failure_events=_load_failure_events(source, origin),
        maintenance_interventions=_load_maintenance_interventions(source, origin),
    )
