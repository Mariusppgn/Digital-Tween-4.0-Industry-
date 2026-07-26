"""Structural parity checks for the bilingual repository README files."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _markdown_structure(path: Path) -> list[str]:
    """Return structural Markdown tokens while ignoring translated prose."""
    structure: list[str] = []
    in_code = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            structure.append(stripped)
        elif in_code:
            structure.append("<code-line>")
        elif re.match(r"^#{1,6}\s", stripped):
            structure.append(stripped.split(maxsplit=1)[0])
        elif stripped.startswith("!["):
            structure.append(re.sub(r"!\[[^\]]*\]", "![alt]", stripped))
        elif stripped.startswith("|"):
            structure.append("|" + "|".join("" for _ in stripped.split("|")[1:-1]) + "|")
        elif re.match(r"^[-*+]\s", stripped):
            structure.append("-")
        elif re.match(r"^\d+\.\s", stripped):
            structure.append("1.")
        elif stripped == "":
            structure.append("")
    return structure


def test_repository_readmes_have_identical_markdown_structure() -> None:
    """English and French README files must keep equivalent Markdown topology."""
    assert _markdown_structure(ROOT / "README.md") == _markdown_structure(ROOT / "README_FR.md")


def test_repository_readmes_keep_identical_technical_links() -> None:
    """Translated README files must preserve link targets in the same order."""
    target_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    english = target_pattern.findall((ROOT / "README.md").read_text(encoding="utf-8"))
    french = target_pattern.findall((ROOT / "README_FR.md").read_text(encoding="utf-8"))
    assert english == french
