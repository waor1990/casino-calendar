"""Unit tests for event oriented callbacks."""

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
def test_toggle_overflow(monkeypatch, casino):
    df = pd.DataFrame(
        {
            "EventName": ["E1"],
            "Casino": [casino],
            "Location": ["Main Hall"],
            "Offer": [""],
            "StartDate": [to_naive_utc(datetime(2025, 4, 14))],
            "EndDate": [to_naive_utc(datetime(2025, 4, 14, 1))],
        }
    )

    app = Dash(__name__)
    register_callbacks(app, df)
    callback = app.callback_map[
        "..overflow-box.className...overflow-toggle.children.."
    ]["callback"].__wrapped__

    monkeypatch.setattr(
        "dash.callback_context", DummyCtx("overflow-toggle"), raising=False
    )
    klass, label = callback(1, "2025-04-13")

    assert klass == "overflow-box-expand show"
    assert "Hide" in label

    monkeypatch.setattr(
        "dash.callback_context", DummyCtx("overflow-toggle"), raising=False
    )
    klass, label = callback(2, "2025-04-13")

    assert klass == "overflow-box-expand"
    assert "Show" in label
