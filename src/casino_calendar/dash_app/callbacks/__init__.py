"""Callback registration package."""

from .events import register_callbacks as _register_event_callbacks
from .filters import register_callbacks as _register_filter_callbacks
from .navigation import register_callbacks as _register_navigation_callbacks
from .theme import register_callbacks as _register_theme_callbacks


def register_callbacks(app, df, repository):
    """Register all callbacks with the Dash app."""
    _register_event_callbacks(app, df, repository)
    _register_filter_callbacks(app, df, repository)
    _register_theme_callbacks(app, df, repository)
    _register_navigation_callbacks(app, df, repository)
