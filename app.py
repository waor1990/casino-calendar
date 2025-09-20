"""Gunicorn entry point for the Casino Calendar Dash application."""

from __future__ import annotations

from casino_calendar.dash_app import create_dash_app
from casino_calendar.dash_app.app import run_app

app, server = create_dash_app()

if __name__ == "__main__":
    run_app(app)
