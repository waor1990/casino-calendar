"""Dash store, helper, and interval builders for the layout."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

import pandas as pd
from dash import dcc, html


def _serialize_value(value: Any) -> Any:
    """Return ``value`` converted to a JSON-serializable representation."""

    if isinstance(value, (datetime, pd.Timestamp)):
        return pd.to_datetime(value).isoformat()

    if isinstance(value, float) and pd.isna(value):
        return None

    if pd.isna(value):  # Handles pd.NA and numpy types
        return None

    return value


def _serialize_events(events: Any | None) -> list[dict[str, Any]]:
    """Return ``events`` as a list of serializable dictionaries."""

    if events is None:
        return []

    records: list[dict[str, Any]] = []

    if isinstance(events, pd.DataFrame):
        for idx, row in events.iterrows():
            record = {key: _serialize_value(value) for key, value in row.items()}
            record["_row_index"] = int(idx)
            records.append(record)
        return records

    if isinstance(events, Iterable):
        for idx, item in enumerate(events):
            if not isinstance(item, dict):
                continue
            record = {key: _serialize_value(value) for key, value in item.items()}
            record.setdefault("_row_index", idx)
            records.append(record)

    return records


def build_state_stores(events: Any | None = None) -> list[dcc.Store]:
    """Return the set of core dcc.Store components used by the app."""

    serialized_events = _serialize_events(events)

    return [
        dcc.Store(id="usable-height", data=600),
        dcc.Store(id="screen-width", data=1024),
        dcc.Store(id="week-offset", data=0),
        dcc.Store(id="overflow-date"),
        dcc.Store(id="animation-refresh"),
        dcc.Store(id="selected-casinos", data=[]),
        dcc.Store(id="selected-event-types", data=[]),
        dcc.Store(id="event-filter-state", data={}),
        dcc.Store(id="legacy-event-data", data=serialized_events),
        dcc.Store(id="event-dataset", data=serialized_events, storage_type="local"),
        dcc.Store(id="selected-event-data"),
        dcc.Store(id="event-edit-mode", data=False),
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
