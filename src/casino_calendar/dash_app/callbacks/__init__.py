"""Callback registration package."""

from .casino_index import register_callbacks as _register_casino_index_callbacks
from .events import register_callbacks as _register_event_callbacks
from .filters import register_callbacks as _register_filter_callbacks
from .navigation import register_callbacks as _register_navigation_callbacks
from .theme import register_callbacks as _register_theme_callbacks


def register_callbacks(app, df):
    """Register all callbacks with the Dash app."""
    _register_casino_index_callbacks(app, df)
    _register_event_callbacks(app, df)
    _register_filter_callbacks(app, df)
    _register_theme_callbacks(app, df)
    _register_navigation_callbacks(app, df)
