"""Regression tests to ensure deprecated imports stay removed."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BANNED_MODULES = ("app_components",)
IMPORT_PATTERN = re.compile(
    r"^\s*(?:from|import)\s+({modules})\b".format(modules="|".join(BANNED_MODULES))
)


def iter_python_files() -> list[Path]:
    files: list[Path] = []
    for directory in ("src", "tests"):
        root = PROJECT_ROOT / directory
        if root.exists():
            files.extend(root.rglob("*.py"))
    return sorted(files)


@pytest.mark.parametrize("python_file", iter_python_files())
def test_no_banned_imports(python_file: Path) -> None:
    """Ensure legacy modules such as ``app_components`` are no longer imported."""
    # ``app_components`` was removed during the package reorganisation; this regression
    # test prevents future imports from silently reintroducing the dependency.
    contents = python_file.read_text(encoding="utf-8")
    matches = [line for line in contents.splitlines() if IMPORT_PATTERN.search(line)]
    assert not matches, "Found deprecated imports in {path}:\n{lines}".format(
        path=python_file.relative_to(PROJECT_ROOT),
        lines="\n".join(matches),
    )
