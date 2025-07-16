"""Callback registration package."""

from .events import register_callbacks as _register_event_callbacks
from .filters import register_callbacks as _register_filter_callbacks


def register_callbacks(app, df):
    """Register all callbacks with the Dash app."""
    _register_event_callbacks(app, df)
    _register_filter_callbacks(app, df)
