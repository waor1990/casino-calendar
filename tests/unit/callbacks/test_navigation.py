"""Unit tests for navigation oriented callbacks."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import pytest
from dash import Dash

from casino_calendar.dash_app.callbacks import register_callbacks
from casino_calendar.dash_app.services.layout_state import to_naive_utc

freeze_time = pytest.importorskip("freezegun").freeze_time


class DummyCtx:
    def __init__(self, triggered_id):
        self.triggered_id = triggered_id
        self.triggered = [{"prop_id": f"{triggered_id}.n_clicks", "value": 1}]


def _navigation_callback(app):
    key = (
        "..week-offset.data...prev-button.disabled...next-button.disabled..."
        "next-button.title.."
    )
    return app.callback_map[key]["callback"].__wrapped__


@freeze_time("2025-04-15")
@pytest.mark.usefixtures("casino")
def test_update_week_offset_next(monkeypatch, casino):
    df = pd.DataFrame(
        {
            "EventName": ["E1", "E2", "E3"],
            "Casino": [casino, casino, casino],
            "Location": ["L", "L", "L"],
            "Offer": ["", "", ""],
            "StartDate": [
                to_naive_utc(datetime(2025, 4, 14)),
                to_naive_utc(datetime(2025, 4, 21)),
                to_naive_utc(datetime(2025, 4, 28)),
            ],
            "EndDate": [
                to_naive_utc(datetime(2025, 4, 14, 1)),
                to_naive_utc(datetime(2025, 4, 21, 1)),
                to_naive_utc(datetime(2025, 4, 28, 1)),
            ],
        }
    )

    app = Dash(__name__)
    register_callbacks(app, df)
    callback = _navigation_callback(app)

    monkeypatch.setattr("dash.callback_context", DummyCtx("next-button"), raising=False)
    offset, prev_disabled, next_disabled, title = callback(0, 1, 0)

    assert offset == 1
    assert not prev_disabled
    assert not next_disabled
    assert title == "Upcoming Week"


@freeze_time("2025-04-15")
@pytest.mark.usefixtures("casino")
def test_update_week_offset_no_next(monkeypatch, casino):
    df = pd.DataFrame(
        {
            "EventName": ["E1"],
            "Casino": [casino],
            "Location": ["L"],
            "Offer": [""],
            "StartDate": [to_naive_utc(datetime(2025, 4, 14))],
            "EndDate": [to_naive_utc(datetime(2025, 4, 14, 1))],
        }
    )

    app = Dash(__name__)
    register_callbacks(app, df)
    callback = _navigation_callback(app)

    monkeypatch.setattr("dash.callback_context", DummyCtx("next-button"), raising=False)
    offset, _, next_disabled, _ = callback(0, 1, 0)

    assert offset == 0
    assert next_disabled
