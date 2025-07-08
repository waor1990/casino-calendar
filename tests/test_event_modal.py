import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

# Ensure package imports work when running tests directly
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # noqa: E402

import pytest  # noqa: E402
from dash import Dash  # noqa: E402
from pytz import timezone  # noqa: E402

from app_components.callbacks import register_callbacks  # noqa: E402
from app_components.data import load_event_data  # noqa: E402
from app_components.layout import create_layout  # noqa: E402
from app_components.plotting import (  # noqa: E402
    annotate_events_with_flags,
    assign_event_rows,
    filter_week_events,
)


class DummyCtx:
    def __init__(self, triggered_id, value):
        self.triggered_id = triggered_id
        self.triggered = [{"value": value}]


def _get_callback():
    df = load_event_data()
    app = Dash(__name__, suppress_callback_exceptions=True)
    app.layout = create_layout(app, df)
    register_callbacks(app, df)
    show_func = None
    for key, val in app.callback_map.items():
        if "event-modal.style" in key:
            show_func = val["callback"].__wrapped__
            break
    return show_func, df


def _get_week_indices(df):
    PDT = timezone("America/Los_Angeles")
    today = datetime.now(PDT)
    current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    week_start = current_sunday
    week_end = week_start + timedelta(days=7)
    week_df = filter_week_events(df, week_start, week_end)
    annot = annotate_events_with_flags(week_df, week_start, week_end)
    assigned = assign_event_rows(annot, week_start)
    return assigned["orig_index"]


def test_event_blocks_open_modal():
    show_func, df = _get_callback()
    indices = _get_week_indices(df)
    if indices.empty:
        pytest.skip("No events found for current week")
    for idx in indices.head(3):
        ctx = DummyCtx({"type": "grid-event", "index": int(idx)}, 1)
        with patch("dash.callback_context", ctx):
            style, cls, body, *_ = show_func(None, None, None, None, [1], 0, 1024)
        assert style == {}
        assert cls == "modal show"
        assert body
