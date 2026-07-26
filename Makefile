.PHONY: install validate simulate report test lint format typecheck check

install:
	uv sync --extra dev

validate:
	uv run asteria validate-config --config configs/scenarios/baseline.yaml

simulate:
	uv run asteria simulate --config configs/scenarios/baseline.yaml --output outputs/baseline

report:
	uv run asteria report --input outputs/baseline --output reports/generated

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy

check: lint typecheck test

