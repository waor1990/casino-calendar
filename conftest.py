"""Repository-wide pytest bootstrap to sanitize import paths early.

This ensures that tests executed from any location (including helper scripts
outside ``tests/``) do not accidentally import NumPy from a local source
checkout or leak user-site packages ahead of the project's virtualenv.
"""

import os
import site
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"


def _strip_numpy_source_paths() -> None:
    """Remove numpy source checkouts from ``sys.path``.

    Windows setups sometimes add a local ``numpy`` repository to ``PYTHONPATH``.
    Importing pandas (or numpy) then fails with the "do not import numpy from
    its source directory" error. Dropping those entries keeps imports using the
    virtualenv-installed wheels.
    """

    for entry in list(sys.path):
        if not entry:
            continue

        path = Path(entry)
        lower_name = path.name.lower()

        if not lower_name.startswith("numpy"):
            continue

        if (path / "setup.py").exists() or (path / "pyproject.toml").exists():
            sys.path.remove(entry)
        elif (path / "numpy").is_dir() and (path / ".git").exists():
            sys.path.remove(entry)


def _strip_user_site_packages() -> None:
    """Remove user-site paths so the virtualenv stays ahead of them."""

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


_strip_numpy_source_paths()
_strip_user_site_packages()

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.environ.setdefault("CASINO_MINIMAL_TEST_LOG", "1")
