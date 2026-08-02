import json
from pathlib import Path

from sylvapapers_digital_twin.cli import build_parser, main
from test_simulation import factory_config, scenario_config

ROOT = Path(__file__).parents[1]


def test_validate_simulate_and_report_commands(tmp_path, capsys):
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "factory": factory_config(),
                "scenario": scenario_config(),
            }
        ),
        encoding="utf-8",
    )
    assert main(["validate-config", "--config", str(config)]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True

    output = tmp_path / "result"
    assert main(["simulate", "--config", str(config), "--output", str(output), "--no-plots"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kpis"]["quantity_produced"] == 0
    assert payload["kpis"]["material_loss_rate"] == 1
    assert (output / "events.csv").exists()

    assert main(["report", "--input", str(output)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["quantity_produced"] == 0
    assert report["material_loss_rate"] == 1


def test_factory_editor_command_has_local_safe_defaults() -> None:
    args = build_parser().parse_args(["factory-editor"])

    assert args.factory == "configs/factory.yaml"
    assert args.host == "127.0.0.1"
    assert args.port == 8765


def test_maintenance_command_consumes_module_a_contract_bundle(tmp_path, capsys) -> None:
    output = tmp_path / "maintenance"

    assert (
        main(
            [
                "maintenance",
                "--input",
                str(ROOT / "data" / "examples" / "maintenance"),
                "--config",
                str(ROOT / "configs" / "maintenance" / "baseline.yaml"),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["machines_assessed"] == 1
    assert payload["recommendations"]["dryer-01"]["policy"] in {
        "corrective",
        "preventive",
        "predictive",
    }
    assert (output / "maintenance_assessments.json").is_file()
