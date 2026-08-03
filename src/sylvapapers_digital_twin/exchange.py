"""Create a compact, verifiable handoff bundle for downstream repositories."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExchangeFile:
    """One public file copied into the inter-repository handoff."""

    name: str
    source: str
    consumers: tuple[str, ...]
    required: bool = True


EXCHANGE_FILES = (
    ExchangeFile("campaign_runs.csv", "campaign", ("module_d", "module_e")),
    ExchangeFile("kpi_statistics.csv", "campaign", ("module_d", "module_e")),
    ExchangeFile("module_d_product_statistics.csv", "campaign", ("module_d",)),
    ExchangeFile("module_e_machine_statistics.csv", "campaign", ("module_e",)),
    ExchangeFile("campaign_metadata.json", "campaign", ("module_d", "module_e")),
    ExchangeFile("column_dictionary.json", "campaign", ("module_d", "module_e")),
    ExchangeFile("machine_decision_features.csv", "maintenance", ("module_d", "module_e")),
    ExchangeFile("maintenance_policy_costs.csv", "maintenance", ("module_e",)),
    ExchangeFile("temporal_validation_metrics.csv", "maintenance", ("module_e",)),
    ExchangeFile("probability_calibration.csv", "maintenance", ("module_e",)),
    ExchangeFile("module_b_manifest.json", "maintenance", ("module_d", "module_e")),
    ExchangeFile("machine_economic_priorities.csv", "economic", ("module_d", "module_e")),
    ExchangeFile("economic_model_feature_importance.csv", "economic", ("module_e",)),
    ExchangeFile("economic_model_metrics.json", "economic", ("module_d", "module_e")),
    ExchangeFile("economic_model_manifest.json", "economic", ("module_d", "module_e")),
)


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _major(version: object) -> str:
    value = str(version).strip()
    if not value or not value.split(".", 1)[0].isdigit():
        raise ValueError(f"Invalid semantic version: {version!r}")
    return value.split(".", 1)[0]


def _csv_details(path: Path) -> tuple[int, list[str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        try:
            columns = next(reader)
        except StopIteration as exc:
            raise ValueError(f"CSV file is empty: {path}") from exc
        if not columns or any(not column.strip() for column in columns):
            raise ValueError(f"CSV header contains an empty column: {path}")
        if len(columns) != len(set(columns)):
            raise ValueError(f"CSV header contains duplicate columns: {path}")
        rows = sum(1 for row in reader if row)
    return rows, columns


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_copy(source: Path, target: Path) -> None:
    temporary = target.with_name(f".{target.name}.tmp")
    shutil.copyfile(source, temporary)
    os.replace(temporary, target)


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def prepare_exchange_bundle(
    campaign_dir: str | Path,
    maintenance_dir: str | Path,
    output_dir: str | Path,
    *,
    economic_model_dir: str | Path | None = None,
) -> dict[str, Path]:
    """Validate and copy only the stable files needed by Modules D and E."""

    sources = {
        "campaign": Path(campaign_dir).resolve(),
        "maintenance": Path(maintenance_dir).resolve(),
        "economic": Path(economic_model_dir).resolve() if economic_model_dir else Path(),
    }
    for label, directory in sources.items():
        if label == "economic" and economic_model_dir is None:
            raise ValueError("economic_model_dir is required for the v2 handoff")
        if not directory.is_dir():
            raise FileNotFoundError(f"{label} output directory not found: {directory}")

    campaign_metadata = _load_object(sources["campaign"] / "campaign_metadata.json")
    maintenance_manifest = _load_object(sources["maintenance"] / "module_b_manifest.json")
    economic_manifest = _load_object(sources["economic"] / "economic_model_manifest.json")
    campaign_schema = str(campaign_metadata.get("schema_version", ""))
    maintenance_schema = str(maintenance_manifest.get("schema_version", ""))
    if _major(campaign_schema) != _major(maintenance_schema):
        raise ValueError(
            "Campaign and maintenance exchange schema major versions are incompatible: "
            f"{campaign_schema!r} != {maintenance_schema!r}"
        )
    campaign_classification = str(campaign_metadata.get("data_classification", ""))
    maintenance_classification = str(maintenance_manifest.get("data_classification", ""))
    if not campaign_classification or campaign_classification != maintenance_classification:
        raise ValueError("Campaign and maintenance data classifications do not match")
    if economic_manifest.get("data_classification") != campaign_classification:
        raise ValueError("Campaign and economic-model data classifications do not match")

    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    manifest_files: list[dict[str, Any]] = []
    paths: dict[str, Path] = {}
    for specification in EXCHANGE_FILES:
        source = sources[specification.source] / specification.name
        if not source.is_file():
            if specification.required:
                raise FileNotFoundError(f"Required exchange file not found: {source}")
            continue
        target = destination / specification.name
        _atomic_copy(source, target)
        row_count: int | None = None
        columns: list[str] | None = None
        if target.suffix.lower() == ".csv":
            row_count, columns = _csv_details(target)
        manifest_files.append(
            {
                "name": specification.name,
                "source_module": specification.source,
                "consumers": list(specification.consumers),
                "bytes": target.stat().st_size,
                "sha256": _sha256(target),
                "row_count": row_count,
                "columns": columns,
            }
        )
        paths[specification.name] = target

    manifest = {
        "schema_version": campaign_schema,
        "producer_version": campaign_metadata.get(
            "producer_version", maintenance_manifest.get("source_code_version", "unknown")
        ),
        "generated_at": datetime.now(UTC).isoformat(),
        "data_classification": campaign_classification,
        "provenance": "sylvapapers_inter_repository_handoff",
        "campaign_id": campaign_metadata.get("campaign_id"),
        "scenario_id": campaign_metadata.get("scenario_id"),
        "source_campaign_generated_at": campaign_metadata.get("generated_at"),
        "source_maintenance_generated_at": maintenance_manifest.get("generated_at"),
        "source_economic_model_generated_at": economic_manifest.get("generated_at"),
        "consumers": ["module_d", "module_e"],
        "files": manifest_files,
        "validation": {
            "schema_major_match": True,
            "data_classification_match": True,
            "csv_headers_unique": True,
            "sha256_algorithm": "SHA-256",
        },
        "limitations": [
            "All reference data are synthetic engineering hypotheses and are not plant-calibrated.",
            "The bundle contains immutable raw inputs; downstream repositories must validate them before use.",
        ],
    }
    manifest_path = destination / "handoff_manifest.json"
    _atomic_json(manifest_path, manifest)
    paths["handoff_manifest.json"] = manifest_path
    return paths
