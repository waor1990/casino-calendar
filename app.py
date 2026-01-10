"""Gunicorn entry point for the Casino Calendar Dash application."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from casino_calendar.bootstrap import bootstrap_environment  # noqa: E402

bootstrap_environment(PROJECT_ROOT)

from casino_calendar.logging.config import setup_logging  # noqa: E402

setup_logging("casino_calendar")

from casino_calendar.dash_app import create_dash_app  # noqa: E402
from casino_calendar.dash_app.app import run_app  # noqa: E402

app, server = create_dash_app()

if __name__ == "__main__":
    run_app(app)
