import csv
import json
from pathlib import Path

import pytest

from sylvapapers_digital_twin.campaign import (
    CampaignConfig,
    load_campaign_config,
    materialize_scenario,
    run_campaign,
    save_campaign,
)
from sylvapapers_digital_twin.cli import main
from sylvapapers_digital_twin.kpi import KPI_NAMES
from test_simulation import factory_config, scenario_config

ROOT = Path(__file__).parents[1]


def _config(tmp_path: Path, *, campaign_id: str = "test-campaign") -> CampaignConfig:
    simulation_config = tmp_path / "simulation.json"
    simulation_config.write_text("{}", encoding="utf-8")
    return CampaignConfig(
        campaign_id=campaign_id,
        simulation_config=simulation_config,
        replications=3,
        seed_start=700,
        seed_step=2,
        effective_scenario_id="test-long-run",
    )


def test_campaign_is_reproducible_and_exports_portable_tables(tmp_path: Path) -> None:
    config = _config(tmp_path)

    first = run_campaign(factory_config(), scenario_config(), config)
    second = run_campaign(factory_config(), scenario_config(), config)

    assert [row["seed"] for row in first.runs] == [700, 702, 704]
    deterministic_columns = [
        "quantity_produced",
        "service_rate",
        "average_cycle_time",
        "total_cost",
    ]
    assert [{key: row[key] for key in deterministic_columns} for row in first.runs] == [
        {key: row[key] for key in deterministic_columns} for row in second.runs
    ]
    assert len(first.statistics) == len(KPI_NAMES)
    assert all(row["n"] == 3 for row in first.statistics)
    assert first.product_statistics
    assert first.machine_statistics

    paths = save_campaign(first, tmp_path / "output", plot=False)
    assert set(paths) == {
        "runs",
        "statistics",
        "module_d_products",
        "module_e_machines",
        "results",
        "metadata",
        "column_dictionary",
        "representative_module_a",
    }
    with paths["runs"].open(encoding="utf-8", newline="") as stream:
        run_rows = list(csv.DictReader(stream))
    assert len(run_rows) == 3
    assert run_rows[0]["schema_version"] == "1.0.0"
    assert run_rows[0]["data_classification"] == "synthetic_hypothesis_not_calibrated"
    dictionary = json.loads(paths["column_dictionary"].read_text(encoding="utf-8"))
    assert set(dictionary["tables"]) == {
        "campaign_runs.csv",
        "kpi_statistics.csv",
        "module_d_product_statistics.csv",
        "module_e_machine_statistics.csv",
    }


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", "\t", "\r"])
def test_campaign_csv_blocks_formula_injection(tmp_path: Path, prefix: str) -> None:
    result = run_campaign(
        factory_config(), scenario_config(), _config(tmp_path, campaign_id=f"{prefix}payload")
    )

    paths = save_campaign(result, tmp_path / "output", plot=False)

    for name in ("runs", "statistics", "module_d_products", "module_e_machines"):
        with paths[name].open(encoding="utf-8", newline="") as stream:
            row = next(csv.DictReader(stream))
        assert row["campaign_id"] == f"'{prefix}payload"


def test_reference_long_run_configuration_is_explicit() -> None:
    config = load_campaign_config(ROOT / "configs" / "campaigns" / "long_run.yaml")

    assert config.replications == 100
    assert config.order_quantity_multiplier == 200
    assert config.horizon_extension_days == 120
    assert config.interarrival_time_minutes == 45
    assert config.campaign_purpose == "economic_reliability_and_lost_revenue_statistics"
    assert config.representative_replication == 4
    assert config.representative_selection_reason == (
        "failure_containing_sample_for_module_b_validation"
    )
    assert len(config.seeds) == 100
    assert len(set(config.seeds)) == 100

    effective = materialize_scenario(scenario_config(), config)
    assert effective["scenario_id"] == "sylvapapers-economic-long-run-01"
    assert effective["interarrival_time"] == 45
    assert sum(order["quantity"] for order in effective["orders"]) == 600


def test_campaign_cli_accepts_an_arbitrary_output_directory(tmp_path: Path, capsys) -> None:
    simulation = tmp_path / "simulation.json"
    simulation.write_text(
        json.dumps({"factory": factory_config(), "scenario": scenario_config()}),
        encoding="utf-8",
    )
    campaign = tmp_path / "campaign.yaml"
    campaign.write_text(
        "\n".join(
            [
                "campaign_id: cli-campaign",
                f"simulation_config: {simulation.name}",
                "replications: 2",
                "seed_start: 10",
            ]
        ),
        encoding="utf-8",
    )
    output = tmp_path / "external-exchange"

    assert (
        main(
            [
                "campaign",
                "--config",
                str(campaign),
                "--output",
                str(output),
                "--no-plot",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["replications"] == 2
    assert (output / "module_d_product_statistics.csv").is_file()
    assert (output / "module_e_machine_statistics.csv").is_file()
