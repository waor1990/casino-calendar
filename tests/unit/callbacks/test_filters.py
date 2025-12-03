"""Unit tests for filter related callbacks."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import pytest
from dash import Dash

from casino_calendar.dash_app.callbacks import register_callbacks
from casino_calendar.dash_app.services.layout_state import to_naive_utc


class DummyCtx:
    def __init__(self, triggered_id):
        self.triggered_id = triggered_id
        self.triggered = [{"prop_id": f"{triggered_id}.n_clicks", "value": 1}]


@pytest.mark.usefixtures("casino")
def test_toggle_casino_filter(monkeypatch, casino):
    other = "Another Casino"
    df = pd.DataFrame({"EventName": ["E1", "E2"], "Casino": [casino, other]})

    app = Dash(__name__)
    register_callbacks(app, df)
    callback = app.callback_map["selected-casinos.data"]["callback"].__wrapped__

    ids = [
        {"type": "casino-filter", "index": casino},
        {"type": "casino-filter", "index": other},
    ]

    monkeypatch.setattr(
        "dash.callback_context",
        DummyCtx({"type": "casino-filter", "index": casino}),
        raising=False,
    )
    selected = callback([1, 0], ids, [])
    assert selected == [casino]

    monkeypatch.setattr(
        "dash.callback_context",
        DummyCtx({"type": "casino-filter", "index": other}),
        raising=False,
    )
    selected = callback([1, 1], ids, selected)
    assert set(selected) == {casino, other}

    monkeypatch.setattr(
        "dash.callback_context",
        DummyCtx({"type": "casino-filter", "index": casino}),
        raising=False,
    )
    selected = callback([2, 1], ids, selected)
    assert selected == [other]


def test_event_type_filter(monkeypatch):
    df = pd.DataFrame(
        {
            "EventName": ["E1", "E2"],
            "Casino": ["A", "A"],
            "Location": ["L", "L"],
            "Offer": ["", ""],
            "StartDate": [
                to_naive_utc(datetime(2025, 4, 14)),
                to_naive_utc(datetime(2025, 4, 14)),
            ],
            "EndDate": [
                to_naive_utc(datetime(2025, 4, 15)),
                to_naive_utc(datetime(2025, 4, 15)),
            ],
            "OfferType": ["Giveaway", "Free-Play"],
        }
    )

    app = Dash(__name__)
    register_callbacks(app, df)
    callback = app.callback_map["calendar-grid.children"]["callback"].__wrapped__

    captured: dict[str, pd.DataFrame] = {}

    def fake_render_week_grid(week_start, filtered_df, screen_width, selected_casinos):
        captured["df"] = filtered_df
        return "grid"

    monkeypatch.setattr(
        "casino_calendar.dash_app.layout.week_grid.render_week_grid",
        fake_render_week_grid,
    )
    monkeypatch.setattr(
        "dash.callback_context",
        DummyCtx({"type": "event-filter", "index": "Giveaway"}),
        raising=False,
    )

    grid = callback(0, 1024, {"Giveaway": True, "Free-Play": True}, df, [], [])
    assert grid == "grid"
    assert len(captured["df"]) == 1
    assert captured["df"].iloc[0]["OfferType"] == "Giveaway"
