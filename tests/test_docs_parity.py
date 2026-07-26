"""Structural checks for bilingual scientific and architecture documentation."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIRS = [
    ("architecture.md", "architecture_FR.md"),
    ("scientific_methodology.md", "scientific_methodology_FR.md"),
    ("data_contracts.md", "data_contracts_FR.md"),
    ("industrial_assumptions.md", "industrial_assumptions_FR.md"),
    ("compute_budget.md", "compute_budget_FR.md"),
    ("module_catalog.md", "module_catalog_FR.md"),
]


def _structure(path: Path) -> tuple[list[str], list[int], list[int]]:
    """Return headings, table widths and fenced-block lengths."""
    headings: list[str] = []
    table_widths: list[int] = []
    block_lengths: list[int] = []
    in_block = False
    current_block_length = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_block:
                block_lengths.append(current_block_length)
                current_block_length = 0
            in_block = not in_block
        elif in_block:
            current_block_length += 1
        elif re.match(r"^#{1,6}\s", stripped):
            headings.append(stripped.split(maxsplit=1)[0])
        elif stripped.startswith("|") and stripped.endswith("|"):
            table_widths.append(stripped.count("|"))
    assert not in_block, f"Unclosed Markdown block in {path}"
    return headings, table_widths, block_lengths


def test_bilingual_documents_keep_equivalent_markdown_topology() -> None:
    """Every English/French pair must preserve headings, tables and fenced blocks."""
    for english_name, french_name in PAIRS:
        assert _structure(ROOT / "docs" / english_name) == _structure(ROOT / "docs" / french_name)
