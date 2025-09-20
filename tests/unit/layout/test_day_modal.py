"""Unit tests for the day modal visualization and callbacks."""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import pytest
from casino_calendar.dash_app.callbacks import register_callbacks
from casino_calendar.dash_app.services.layout_state import to_naive_utc
from casino_calendar.dash_app.visualization import charts as day_charts
from casino_calendar.services import data_parsing
from casino_calendar.services.colors import get_color
from dash import Dash


class DummyCtx:
    """Minimal stand-in for Dash's callback context."""

    def __init__(self, triggered_id):
        self.triggered_id = triggered_id
        self.triggered = [{"prop_id": f"{triggered_id}.n_clicks", "value": 1}]


def _event_modal_callback(casino: str):
    df = pd.DataFrame(
        {
            "EventName": ["Weekend Bash"],
            "Casino": [casino],
            "Location": ["Main Hall"],
            "Offer": [""],
            "StartDate": [to_naive_utc(datetime(2025, 7, 12, 10))],
            "EndDate": [to_naive_utc(datetime(2025, 7, 13, 2))],
        }
    )
    app = Dash(__name__)
    register_callbacks(app, df)
    key = "".join(
        [
            "..event-modal.style...event-modal.className...event-modal-body.children",
            "...close-timer.n_intervals...day-modal.style...day-modal.className...",
            "day-modal-body.children..",
        ]
    )
    return app.callback_map[key]["callback"].__wrapped__


@pytest.mark.usefixtures("casino")
def test_show_event_modal_handles_duplicate(monkeypatch, casino):
    callback = _event_modal_callback(casino)

    def fake_prepare(events_df, week_start):
        return data_parsing.prepare_week_events(
            events_df, week_start, include_sunday_duplicates=True
        )

    monkeypatch.setattr(
        "casino_calendar.services.data_parsing.prepare_week_events", fake_prepare
    )
    monkeypatch.setattr(
        "dash.callback_context",
        DummyCtx({"type": "grid-event", "index": 0}),
        raising=False,
    )

    result = callback(None, 0, 0, 0, [1], [0], 0, 1024, [])
    assert result[1] == "modal show"
    assert result[4] == {"display": "none"}


@pytest.mark.usefixtures("casino")
def test_show_event_modal_close(monkeypatch, casino):
    callback = _event_modal_callback(casino)
    monkeypatch.setattr("dash.callback_context", DummyCtx("close-modal"), raising=False)

    result = callback(None, 1, 0, 0, [0], [0], 0, 1024, [])
    assert result[1] == "modal closing"
    assert result[3] == 1


def _build_boundary_events(clicked_date):
    return pd.DataFrame(
        [
            {
                "EventName": "Starts Today",
                "Casino": "ilani",
                "Location": "",
                "OfferType": "",
                "Offer": "Starts today",
                "StartDate": clicked_date.replace(hour=17),
                "EndDate": clicked_date.replace(hour=19) + timedelta(days=1),
            },
            {
                "EventName": "Ends Today",
                "Casino": "ilani",
                "Location": "",
                "OfferType": "",
                "Offer": "Ends today",
                "StartDate": clicked_date.replace(hour=15) - timedelta(days=1),
                "EndDate": clicked_date.replace(hour=23),
            },
            {
                "EventName": "Same Day",
                "Casino": "ilani",
                "Location": "",
                "OfferType": "",
                "Offer": "Same day",
                "StartDate": clicked_date.replace(hour=16),
                "EndDate": clicked_date.replace(hour=0) + timedelta(days=1),
            },
            {
                "EventName": "Starts Midnight",
                "Casino": "ilani",
                "Location": "",
                "OfferType": "",
                "Offer": "Starts midnight",
                "StartDate": clicked_date.replace(hour=7),
                "EndDate": clicked_date.replace(hour=13),
            },
            {
                "EventName": "Ends Midnight",
                "Casino": "ilani",
                "Location": "",
                "OfferType": "",
                "Offer": "Ends midnight",
                "StartDate": clicked_date.replace(hour=1) - timedelta(days=1),
                "EndDate": clicked_date.replace(hour=7),
            },
        ]
    )


def _collect_event_titles(elements):
    grid = elements[1]
    event_blocks = [
        child
        for child in getattr(grid, "children", [])
        if getattr(child, "className", "") and "event-block-day" in child.className
    ]
    return [getattr(block, "title", "") for block in event_blocks]


def test_day_modal_boundary_cases():
    clicked_date = to_naive_utc(datetime(2025, 8, 5))
    events = _build_boundary_events(clicked_date)

    elements = day_charts.generate_day_view_html(events, clicked_date, get_color, 1024)
    titles = _collect_event_titles(elements)

    assert len(titles) == 5
    assert set(titles) == {
        "Starts Today",
        "Ends Today",
        "Same Day",
        "Starts Midnight",
        "Ends Midnight",
    }


def test_day_modal_midnight_boundary_edge_case():
    clicked_date = to_naive_utc(datetime(2025, 8, 5))
    events = pd.DataFrame(
        [
            {
                "EventName": "Ends At Midnight",
                "Casino": "ilani",
                "Location": "",
                "OfferType": "",
                "Offer": "Boundary",
                "StartDate": clicked_date.replace(hour=1) - timedelta(days=1),
                "EndDate": clicked_date.replace(hour=7),
            }
        ]
    )

    elements = day_charts.generate_day_view_html(events, clicked_date, get_color, 1024)
    titles = _collect_event_titles(elements)

    assert titles == ["Ends At Midnight"]


def test_day_modal_sorting_orders_by_time_then_name_then_category():
    clicked_date = datetime(2025, 8, 6)
    events = pd.DataFrame(
        [
            {
                "EventName": "Late Event",
                "Casino": "Casino B",
                "OfferType": "Giveaway",
                "Offer": "Late event",
                "StartDate": pd.Timestamp("2025-08-06 18:00:00"),
                "EndDate": pd.Timestamp("2025-08-06 20:00:00"),
            },
            {
                "EventName": "Early Event Z Casino",
                "Casino": "Casino Z",
                "OfferType": "Free-Play",
                "Offer": "Early event Z",
                "StartDate": pd.Timestamp("2025-08-06 10:00:00"),
                "EndDate": pd.Timestamp("2025-08-06 12:00:00"),
            },
            {
                "EventName": "Early Event A Casino",
                "Casino": "Casino A",
                "OfferType": "Point-Based",
                "Offer": "Early event A",
                "StartDate": pd.Timestamp("2025-08-06 10:00:00"),
                "EndDate": pd.Timestamp("2025-08-06 12:00:00"),
            },
            {
                "EventName": "Same Casino Different Category 1",
                "Casino": "Casino A",
                "OfferType": "Free-Play",
                "Offer": "Same casino category 1",
                "StartDate": pd.Timestamp("2025-08-06 14:00:00"),
                "EndDate": pd.Timestamp("2025-08-06 16:00:00"),
            },
            {
                "EventName": "Same Casino Different Category 2",
                "Casino": "Casino A",
                "OfferType": "Point-Based",
                "Offer": "Same casino category 2",
                "StartDate": pd.Timestamp("2025-08-06 14:00:00"),
                "EndDate": pd.Timestamp("2025-08-06 16:00:00"),
            },
        ]
    )

    elements = day_charts.generate_day_view_html(events, clicked_date, get_color, 1024)
    titles = _collect_event_titles(elements)

    assert titles == [
        "Early Event A Casino",
        "Early Event Z Casino",
        "Same Casino Different Category 1",
        "Same Casino Different Category 2",
        "Late Event",
    ]
