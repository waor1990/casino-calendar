"""Reusable Dash store and helper components."""

from __future__ import annotations

from dash import dcc, html


def build_state_stores() -> list[dcc.Store]:
    """Return the set of core dcc.Store components used by the app."""

    return [
        dcc.Store(id="usable-height", data=600),
        dcc.Store(id="screen-width", data=1024),
        dcc.Store(id="week-offset", data=0),
        dcc.Store(id="overflow-date"),
        dcc.Store(id="animation-refresh"),
        dcc.Store(id="selected-casinos", data=[]),
        dcc.Store(id="selected-event-types", data=[]),
        dcc.Store(id="event-filter-state", data={}),
        dcc.Store(id="legacy-event-data"),
        dcc.Store(id="last-day-date", data=None),
        dcc.Store(id="reopen-day-on-close", data=False),
        dcc.Store(id="theme-store", data="light", storage_type="local"),
    ]


def build_hidden_helpers() -> list[html.Div]:
    """Return hidden divs used for triggering callbacks."""

    return [
        html.Div(id="theme-dummy", style={"display": "none"}),
        html.Div(id="animation-dummy", style={"display": "none"}),
    ]


def build_intervals() -> list[dcc.Interval]:
    """Return interval timers for asynchronous triggers."""

    return [
        dcc.Interval(id="initial-trigger", interval=1, max_intervals=1),
        dcc.Interval(
            id="close-timer",
            interval=600,
            n_intervals=0,
            disabled=True,
        ),
    ]


__all__ = ["build_hidden_helpers", "build_intervals", "build_state_stores"]
