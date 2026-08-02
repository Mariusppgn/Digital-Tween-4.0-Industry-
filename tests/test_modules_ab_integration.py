from __future__ import annotations

from pathlib import Path

from sylvapapers_contracts import load_factory_config, load_simulation_scenario
from sylvapapers_digital_twin import save_result, simulate
from sylvapapers_maintenance import analyze_maintenance_bundle, save_maintenance_analysis

ROOT = Path(__file__).parents[1]


def test_reference_digital_twin_bundle_flows_into_predictive_maintenance(
    tmp_path: Path,
) -> None:
    factory = load_factory_config(ROOT / "configs" / "factory.yaml")
    scenario = load_simulation_scenario(ROOT / "data" / "examples" / "simulation_scenario.json")
    module_a_output = tmp_path / "module-a"
    module_b_output = tmp_path / "module-b"

    result = simulate(factory, scenario)
    save_result(result, module_a_output, plots=False)
    analysis = analyze_maintenance_bundle(
        module_a_output,
        ROOT / "configs" / "maintenance" / "baseline.yaml",
    )
    paths = save_maintenance_analysis(analysis, module_b_output)

    sensor_machines = {record["machine_id"] for record in result.sensor_records}
    assessed_machines = {assessment.machine_id for assessment in analysis.assessments}
    assert len(result.jobs) == 10
    assert result.final_state["work_in_progress"] == 0
    assert assessed_machines == sensor_machines - {"chips-buffer"}
    assert all(
        assessment.recommendation.policy in {"corrective", "preventive", "predictive"}
        for assessment in analysis.assessments
    )
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths.values())
