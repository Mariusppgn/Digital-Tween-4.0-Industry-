.PHONY: install validate simulate maintenance editor report test lint format typecheck check

install:
	uv sync --extra dev

validate:
	uv run sylvapapers validate-config --config configs/scenarios/baseline.yaml

simulate:
	uv run sylvapapers simulate --config configs/scenarios/baseline.yaml --output outputs/baseline

maintenance: simulate
	uv run sylvapapers maintenance --input outputs/baseline --output outputs/maintenance

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
