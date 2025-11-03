"""Unit tests for the weekly calendar grid."""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import pytest
from dash import Dash

from casino_calendar.dash_app.callbacks import register_callbacks
from casino_calendar.dash_app.layout.week_grid import _build_block
from casino_calendar.dash_app.services.layout_state import to_naive_utc
from casino_calendar.services.data_parsing import prepare_week_events

freeze_time = pytest.importorskip("freezegun").freeze_time


@pytest.mark.usefixtures("casino")
def test_prepare_week_events_flags_boundary_events(casino):
    week_start = to_naive_utc(datetime(2025, 7, 6))
    df = pd.DataFrame(
        {
            "EventName": ["Left", "Right", "Full"],
            "Casino": [casino] * 3,
            "StartDate": [
                week_start - timedelta(days=1),
                week_start + timedelta(days=5),
                week_start - timedelta(days=1),
            ],
            "EndDate": [
                week_start + timedelta(hours=2),
                week_start + timedelta(days=7, hours=2),
                week_start + timedelta(days=8),
            ],
        }
    )

    result = prepare_week_events(df, week_start)

    names = list(result["EventName"])
    assert names == ["Left", "Right"]

    left = result[result["EventName"] == "Left"].iloc[0]
    right = result[result["EventName"] == "Right"].iloc[0]

    assert left["has_left_arrow"] and not left["has_right_arrow"]
    assert right["has_right_arrow"] and not right["has_left_arrow"]


@pytest.mark.usefixtures("casino")
def test_build_block_breakpoints(casino):
    week_start = to_naive_utc(datetime(2025, 7, 6))
    week_end = week_start + timedelta(days=7)
    row = {
        "EventName": "This is a very long event name for testing breakpoints",
        "Casino": casino,
        "row_num": 0,
        "StartDate": week_start + timedelta(days=1),
        "EndDate": week_start + timedelta(days=3),
        "has_left_arrow": False,
        "has_right_arrow": False,
    }
    colors = {casino: {"bg": "#fff", "text": "#000"}}

    mobile_text, _, _, _ = _build_block(row, week_start, week_end, 375, colors)
    tablet_text, _, _, _ = _build_block(row, week_start, week_end, 650, colors)
    desktop_text, _, _, _ = _build_block(row, week_start, week_end, 1024, colors)

    assert len(mobile_text) <= len(tablet_text) <= len(desktop_text)


@freeze_time("2025-04-15")
def test_week_label_matches_grid():
    app = Dash(__name__)
    register_callbacks(app, pd.DataFrame())
    func = app.callback_map["week-label.children"]["callback"].__wrapped__
    label = func(0)
    assert label == "Events for the Week of April 13 - April 19, 2025"
