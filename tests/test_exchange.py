from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from sylvapapers_digital_twin import prepare_exchange_bundle
from sylvapapers_digital_twin.exchange import EXCHANGE_FILES


def _write_sources(
    root: Path, maintenance_classification: str | None = None
) -> tuple[Path, Path, Path]:
    campaign = root / "campaign"
    maintenance = root / "maintenance"
    economic = root / "economic"
    campaign.mkdir()
    maintenance.mkdir()
    economic.mkdir()
    classification = "synthetic_hypothesis_not_calibrated"
    (campaign / "campaign_metadata.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "producer_version": "0.4.0",
                "generated_at": "2026-08-03T10:00:00+00:00",
                "data_classification": classification,
                "campaign_id": "campaign-test",
                "scenario_id": "scenario-test",
            }
        ),
        encoding="utf-8",
    )
    (campaign / "column_dictionary.json").write_text(
        json.dumps({"schema_version": "1.0.0"}), encoding="utf-8"
    )
    (maintenance / "module_b_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "source_code_version": "0.4.0",
                "generated_at": "2026-08-03T10:05:00+00:00",
                "data_classification": maintenance_classification or classification,
            }
        ),
        encoding="utf-8",
    )
    (economic / "economic_model_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "source_code_version": "0.5.0",
                "generated_at": "2026-08-03T10:06:00+00:00",
                "data_classification": classification,
            }
        ),
        encoding="utf-8",
    )
    for specification in EXCHANGE_FILES:
        source = {"campaign": campaign, "maintenance": maintenance, "economic": economic}[
            specification.source
        ]
        path = source / specification.name
        if path.exists():
            continue
        if path.suffix == ".csv":
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["schema_version", "data_classification", "value"])
                writer.writerow(["1.0.0", classification, "42"])
        elif path.suffix == ".json":
            path.write_text(json.dumps({"schema_version": "1.0.0"}), encoding="utf-8")
    return campaign, maintenance, economic


def test_prepare_exchange_bundle_copies_validated_files_with_checksums(tmp_path: Path) -> None:
    campaign, maintenance, economic = _write_sources(tmp_path)

    paths = prepare_exchange_bundle(
        campaign, maintenance, tmp_path / "handoff", economic_model_dir=economic
    )

    assert len(paths) == len(EXCHANGE_FILES) + 1
    manifest = json.loads(paths["handoff_manifest.json"].read_text(encoding="utf-8"))
    assert manifest["producer_version"] == "0.4.0"
    assert manifest["campaign_id"] == "campaign-test"
    assert manifest["validation"]["schema_major_match"] is True
    assert len(manifest["files"]) == len(EXCHANGE_FILES)
    csv_entry = next(item for item in manifest["files"] if item["name"] == "campaign_runs.csv")
    assert csv_entry["row_count"] == 1
    assert csv_entry["columns"] == ["schema_version", "data_classification", "value"]
    assert len(csv_entry["sha256"]) == 64
    assert not list((tmp_path / "handoff").glob(".*.tmp"))


def test_prepare_exchange_bundle_rejects_classification_mismatch(tmp_path: Path) -> None:
    campaign, maintenance, economic = _write_sources(tmp_path, "real_plant_data")

    with pytest.raises(ValueError, match="classifications do not match"):
        prepare_exchange_bundle(
            campaign, maintenance, tmp_path / "handoff", economic_model_dir=economic
        )
