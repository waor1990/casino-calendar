"""Common bootstrap utilities for runtime and test entrypoints."""

from __future__ import annotations

import os
import site
import sys
import sysconfig
from pathlib import Path
from typing import Iterable


def strip_numpy_source_paths() -> None:
    """Remove numpy source checkouts from ``sys.path``.

    Environments that have a local numpy repository on ``PYTHONPATH`` will fail
    when pandas attempts to import numpy, raising the familiar
    ``"do not import numpy from its source directory"`` error. Cleaning those
    entries ensures the virtualenv wheels are used instead.
    """

    allowed_prefixes = _allowed_site_prefixes()

    for entry in list(sys.path):
        path = _safe_path(entry)
        if path is None:
            continue

        if _is_under_allowed_prefix(path, allowed_prefixes):
            continue

        if _looks_like_numpy_checkout(path):
            try:
                sys.path.remove(entry)
            except ValueError:
                # Entry may have been removed by a previous pass.
                continue


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


def _safe_path(entry: str | os.PathLike[str] | None) -> Path | None:
    if not entry:
        return None
    try:
        return Path(entry).resolve()
    except Exception:
        return None


def _allowed_site_prefixes() -> tuple[Path, ...]:
    candidates: list[str] = []
    try:
        site_paths = sysconfig.get_paths()
        for key in ("purelib", "platlib"):
            candidate = site_paths.get(key)
            if candidate:
                candidates.append(candidate)
    except Exception:
        pass

    for site_dir in site.getsitepackages() or []:
        candidates.append(site_dir)

    resolved: list[Path] = []
    for candidate in candidates:
        try:
            resolved.append(Path(candidate).resolve())
        except Exception:
            continue
    return tuple(resolved)


def _is_under_allowed_prefix(path: Path, allowed_prefixes: Iterable[Path]) -> bool:
    for prefix in allowed_prefixes:
        try:
            if path.is_relative_to(prefix):
                return True
        except ValueError:
            continue
        except AttributeError:
            # Python <3.9 fallback
            try:
                path.relative_to(prefix)
                return True
            except Exception:
                continue
    return False


def _looks_like_numpy_checkout(path: Path) -> bool:
    """Return True when the path resembles a local NumPy source checkout."""

    parts_lower = {part.lower() for part in path.parts}
    if any(part == "numpy" or part.startswith("numpy-") for part in parts_lower):
        return True

    if (path / "setup.py").exists() or (path / "pyproject.toml").exists():
        numpy_dir = path / "numpy"
        if numpy_dir.is_dir() and (numpy_dir / "__init__.py").exists():
            return True

    candidate = path / "numpy"
    if candidate.is_dir() and (candidate / "__init__.py").exists():
        return True

    return False


__all__ = [
    "bootstrap_environment",
    "ensure_project_paths",
    "strip_numpy_source_paths",
    "strip_user_site_packages",
]
