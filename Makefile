.PHONY: install validate simulate campaign exchange maintenance economic-model editor report test lint format typecheck check

install:
	uv sync --extra dev

validate:
	uv run sylvapapers validate-config --config configs/scenarios/baseline.yaml

simulate:
	uv run sylvapapers simulate --config configs/scenarios/baseline.yaml --output outputs/baseline

campaign:
	uv run sylvapapers campaign --config configs/campaigns/long_run.yaml --output outputs/long-run

exchange:
	uv run sylvapapers campaign --config configs/campaigns/long_run.yaml --output outputs/long-run-statistics
	uv run sylvapapers maintenance --input outputs/long-run-statistics/representative_module_a --output outputs/long-run-maintenance --config configs/maintenance/baseline.yaml
	uv run sylvapapers economic-model --input outputs/long-run-statistics/module_e_machine_statistics.csv --output outputs/economic-model
	uv run sylvapapers prepare-exchange --campaign outputs/long-run-statistics --maintenance outputs/long-run-maintenance --economic-model outputs/economic-model --output exports/sylvapapers-handoff-v2

maintenance: simulate
	uv run sylvapapers maintenance --input outputs/baseline --output outputs/maintenance

economic-model:
	uv run sylvapapers economic-model --input outputs/long-run-statistics/module_e_machine_statistics.csv --output outputs/economic-model

editor:
	uv run sylvapapers factory-editor --factory configs/factory.yaml

report:
	uv run sylvapapers report --input outputs/baseline --output reports/generated

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy

check: lint typecheck test
