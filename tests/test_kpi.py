from asteria_digital_twin import KPI_NAMES, calculate_kpis, save_result, simulate
from test_simulation import factory_config, scenario_config


def test_factory_kpis_and_csv_json_exports(tmp_path):
    result = simulate(factory_config(), scenario_config())
    kpis = calculate_kpis(result)
    assert tuple(kpis) == KPI_NAMES
    assert len(kpis) == 11
    assert kpis["quantity_produced"] == 0
    assert kpis["material_loss_rate"] == 1
    assert kpis["downtime"] > 0
    assert kpis["total_cost"] > 0
    assert kpis["energy_consumption"] > 0
    assert 0 <= kpis["simplified_oee"] <= 1

    paths = save_result(result, tmp_path, plots=False)
    assert {path.name for path in paths.values()} == {
        "events.csv",
        "jobs.csv",
        "kpis.json",
        "summary.json",
    }
    assert all(path.is_file() for path in paths.values())
