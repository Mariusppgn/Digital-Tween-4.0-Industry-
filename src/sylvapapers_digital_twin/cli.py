"""Command-line interface for validation, simulation and reporting."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import networkx as nx
import yaml

from .graph import build_process_graph
from .kpi import calculate_kpis
from .reporting import generate_markdown_report, save_result
from .simulator import simulate


def _read_document(path: Path) -> Any:
    """Load one UTF-8 JSON or YAML document."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    raise ValueError(f"Unsupported configuration format: {path.suffix}")


def _contract_inputs(
    factory_path: str | Path,
    scenario_path: str | Path,
    product_path: str | Path | None,
) -> tuple[Any, Any, Any]:
    """Load separately versioned contract files."""
    try:
        import sylvapapers_contracts as contracts
    except ImportError as exc:
        raise RuntimeError("sylvapapers_contracts must be installed to load contract files") from exc
    factory = contracts.load_factory_config(factory_path)
    scenario = contracts.load_simulation_scenario(scenario_path)
    product = (
        contracts.load_model(product_path, contracts.ProductDefinition) if product_path else None
    )
    return factory, scenario, product


def _inputs(args: argparse.Namespace) -> tuple[Any, Any, Any]:
    """Resolve either a combined configuration or separate contract files."""
    if args.config:
        config_path = Path(args.config).resolve()
        data = _read_document(config_path)
        if not isinstance(data, Mapping):
            raise ValueError("Combined configuration must be a mapping")
        factory_value = data.get("factory")
        scenario_value = data.get("scenario")
        product_value = data.get("product")
        if isinstance(factory_value, str) and isinstance(scenario_value, str):
            base = config_path.parent
            return _contract_inputs(
                (base / factory_value).resolve(),
                (base / scenario_value).resolve(),
                (base / product_value).resolve() if isinstance(product_value, str) else None,
            )
        if factory_value is None or scenario_value is None:
            raise ValueError("Combined configuration requires factory and scenario")
        return factory_value, scenario_value, product_value
    if not args.factory or not args.scenario:
        raise ValueError("Provide --config or both --factory and --scenario")
    return _contract_inputs(args.factory, args.scenario, args.product)


def _input_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="Combined YAML/JSON configuration")
    parser.add_argument("--factory", help="FactoryConfig YAML/JSON")
    parser.add_argument("--scenario", help="SimulationScenario YAML/JSON")
    parser.add_argument("--product", help="Optional ProductDefinition YAML/JSON")


def build_parser() -> argparse.ArgumentParser:
    """Build the public CLI parser."""
    parser = argparse.ArgumentParser(prog="sylvapapers", description="SylvaPapers paper-mill twin")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-config", help="Validate contracts and graph")
    _input_arguments(validate)
    run = commands.add_parser("simulate", help="Execute a seeded digital-twin scenario")
    _input_arguments(run)
    run.add_argument("--output", default="outputs/baseline")
    run.add_argument("--no-plots", action="store_true")
    report = commands.add_parser("report", help="Create a Markdown report from saved results")
    report.add_argument("--input", default="outputs/baseline")
    report.add_argument("--output")
    editor = commands.add_parser("factory-editor", help="Serve the local visual factory editor")
    editor.add_argument("--factory", default="configs/factory.yaml")
    editor.add_argument("--host", default="127.0.0.1")
    editor.add_argument("--port", type=int, default=8765)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the selected command and return a process exit code."""
    args = build_parser().parse_args(argv)
    if args.command == "factory-editor":
        from .web.server import main as editor_main

        return editor_main(
            ["--config", args.factory, "--host", args.host, "--port", str(args.port)]
        )
    if args.command == "report":
        if args.output:
            generate_markdown_report(args.input, args.output)
        print((Path(args.input) / "kpis.json").read_text(encoding="utf-8"))
        return 0
    factory, scenario, product = _inputs(args)
    graph = build_process_graph(factory)
    if args.command == "validate-config":
        print(
            json.dumps(
                {
                    "valid": True,
                    "nodes": len(graph),
                    "edges": graph.number_of_edges(),
                    "has_cycle": not nx.is_directed_acyclic_graph(graph),
                }
            )
        )
        return 0
    result = simulate(factory, scenario, product)
    paths = save_result(result, args.output, plots=not args.no_plots)
    print(
        json.dumps(
            {
                "kpis": calculate_kpis(result),
                "runtime_seconds": result.runtime_seconds,
                "files": {name: str(path) for name, path in paths.items()},
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
