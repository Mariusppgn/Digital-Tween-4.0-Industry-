import json

from asteria_digital_twin.cli import main
from test_simulation import factory_config, scenario_config


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
