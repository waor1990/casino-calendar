from datetime import datetime

import pandas as pd
from dash import Dash

from app_components.callbacks import register_callbacks
from app_components.utils import to_naive_utc
from utils import data_parsing


class DummyCtx:
    def __init__(self, triggered_id):
        self.triggered_id = triggered_id
        self.triggered = [{"prop_id": f"{triggered_id}.n_clicks", "value": 1}]


def _create_app():
    df = pd.DataFrame(
        {
            "EventName": ["Weekend Bash"],
            "Casino": ["ilani"],
            "Location": [""],
            "Offer": [""],
            "StartDate": [to_naive_utc(datetime(2025, 7, 12, 10))],
            "EndDate": [to_naive_utc(datetime(2025, 7, 13, 2))],
        }
    )
    app = Dash(__name__)
    register_callbacks(app, df)
    key = (
        "..event-modal.style...event-modal.className...event-modal-body.children"
        "...close-timer.n_intervals...day-modal.style...day-modal.className...day-modal-body.children.."
    )
    func = app.callback_map[key]["callback"].__wrapped__
    return func


def test_show_event_modal_handles_duplicate(monkeypatch):
    func = _create_app()

    def fake_prepare(events_df, week_start):
        return data_parsing.prepare_week_events(
            events_df, week_start, include_sunday_duplicates=True
        )

    monkeypatch.setattr(
        "app_components.callbacks.events.prepare_week_events", fake_prepare
    )
    monkeypatch.setattr(
        "dash.callback_context",
        DummyCtx({"type": "grid-event", "index": 0}),
        raising=False,
    )

    result = func(None, 0, 0, 0, [1], [0], 0, 1024)
    assert result[1] == "modal show"
    assert result[4] == {"display": "none"}


def test_show_event_modal_close(monkeypatch):
    func = _create_app()
    monkeypatch.setattr("dash.callback_context", DummyCtx("close-modal"), raising=False)

    result = func(None, 1, 0, 0, [0], [0], 0, 1024)
    assert result[1] == "modal closing"
    assert result[3] == 1
