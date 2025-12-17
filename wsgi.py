"""WSGI entrypoint for compatible hosting environments."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Tuple, cast

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from casino_calendar.bootstrap import bootstrap_environment

bootstrap_environment(PROJECT_ROOT)

CreateDashAppType = Callable[[], Tuple[Any, Any]]

create_dash_app = cast(
    CreateDashAppType,
    getattr(import_module("casino_calendar.dash_app.app"), "create_dash_app"),
)

app, server = create_dash_app()
application = server
