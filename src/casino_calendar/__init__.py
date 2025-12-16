"""Casino Calendar application package."""

from __future__ import annotations

from typing import Any


def create_dash_app(*args: Any, **kwargs: Any):
    """Lazily import and create the Dash application instance."""

    from .dash_app import create_dash_app as _create_dash_app

    return _create_dash_app(*args, **kwargs)


def run_app(*args: Any, **kwargs: Any):
    """Lazily import and run the Dash application server."""

    from .dash_app import run_app as _run_app

    return _run_app(*args, **kwargs)


__all__ = ["create_dash_app", "run_app"]
