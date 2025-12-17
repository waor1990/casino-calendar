"""Common bootstrap utilities for runtime and test entrypoints."""

from __future__ import annotations

import os
import site
import sys
from pathlib import Path


def strip_numpy_source_paths() -> None:
    """Remove numpy source checkouts from ``sys.path``.

    Environments that have a local numpy repository on ``PYTHONPATH`` will fail
    when pandas attempts to import numpy, raising the familiar
    ``"do not import numpy from its source directory"`` error. Cleaning those
    entries ensures the virtualenv wheels are used instead.
    """

    for entry in list(sys.path):
        if not entry:
            continue

        path = Path(entry)
        lower_name = path.name.lower()

        if "numpy" not in lower_name:
            continue

        if (path / "setup.py").exists() or (path / "pyproject.toml").exists():
            sys.path.remove(entry)
        elif (path / "numpy").is_dir() and (path / ".git").exists():
            sys.path.remove(entry)


def strip_user_site_packages() -> None:
    """Remove user-site entries so the project virtualenv stays first."""

    try:
        user_sites = site.getusersitepackages()
    except Exception:
        return

    if isinstance(user_sites, str):
        user_sites = [user_sites]

    normalized = {Path(p).resolve() for p in user_sites if p}
    for entry in list(sys.path):
        try:
            resolved = Path(entry).resolve()
        except Exception:
            continue
        if resolved in normalized:
            sys.path.remove(entry)


def ensure_project_paths(project_root: Path) -> None:
    """Ensure the project root and ``src`` directory are on ``sys.path``."""

    src_dir = project_root / "src"
    for path in (src_dir, project_root):
        if path.is_dir():
            path_str = str(path)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)


def bootstrap_environment(project_root: Path) -> None:
    """Apply standard environment fixes for app and tests."""

    strip_numpy_source_paths()
    strip_user_site_packages()
    ensure_project_paths(project_root)
    os.environ.setdefault("PYTHONNOUSERSITE", "1")


__all__ = [
    "bootstrap_environment",
    "ensure_project_paths",
    "strip_numpy_source_paths",
    "strip_user_site_packages",
]
