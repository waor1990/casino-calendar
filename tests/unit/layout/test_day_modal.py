"""Unit tests for the day modal visualization and callbacks."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import dash
import pandas as pd
import pytest
from casino_calendar.dash_app.callbacks import register_callbacks
from casino_calendar.dash_app.services.layout_state import to_naive_utc
from casino_calendar.dash_app.visualization import charts as day_charts
from casino_calendar.services import data_parsing
from casino_calendar.services.colors import get_color
from dash import Dash, no_update


class DummyCtx:
    """Minimal stand-in for Dash's callback context."""

    def __init__(self, triggered_id, value=1, states=None, prop="n_clicks"):
        self.triggered_id = triggered_id
        if isinstance(triggered_id, dict):
            trigger_key = json.dumps(triggered_id, separators=(",", ":"))
        else:
            trigger_key = triggered_id
        self.triggered = [{"prop_id": f"{trigger_key}.{prop}", "value": value}]
        self.states = states or {}


class TimerCtx:
    """Context helper for timer-triggered callbacks."""

    def __init__(self, value: int = 1):
        self.triggered_id = "close-timer"
        self.triggered = [{"prop_id": "close-timer.n_intervals", "value": value}]


def _event_modal_callback(casino: str):
    df = pd.DataFrame(
        {
            "EventName": ["Weekend Bash"],
            "Casino": [casino],
            "Location": ["Main Hall"],
            "OfferType": [""],
            "Offer": [""],
            "StartDate": [to_naive_utc(datetime(2025, 7, 12, 10))],
            "EndDate": [to_naive_utc(datetime(2025, 7, 13, 2))],
        }
    )
    app = Dash(__name__)
    register_callbacks(app, df)
    for key, details in app.callback_map.items():
        if (
            "event-modal.style" in key
            and "event-modal.className" in key
            and "event-modal-body.children" in key
            and "close-timer.n_intervals" in key
        ):
            return details["callback"].__wrapped__
    raise KeyError("Event modal callback not registered")


GRID_EVENT_IDS = [{"type": "grid-event", "index": 0}]
DAY_COLUMN_IDS = [{"type": "day-column", "index": "2025-07-12"}]


def _unpack_modal_outputs(result):
    (
        modal_style,
        modal_class,
        modal_body,
        form_children,
        footer_open,
        context_payload,
        close_timer_n,
        close_timer_disabled,
        day_modal_style,
        day_modal_class,
        day_modal_body,
        *extra,
    ) = result

    status_children = status_class = None
    if len(extra) == 2:
        status_children, status_class = extra

    return {
        "modal_style": modal_style,
        "modal_class": modal_class,
        "modal_body": modal_body,
        "form_children": form_children,
        "footer_open": footer_open,
        "context_payload": context_payload,
        "close_timer_n": close_timer_n,
        "close_timer_disabled": close_timer_disabled,
        "day_modal_style": day_modal_style,
        "day_modal_class": day_modal_class,
        "day_modal_body": day_modal_body,
        "status_children": status_children,
        "status_class": status_class,
    }


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

    result = callback(
        None,
        0,
        0,
        0,
        [1],
        [0],
        [1111],
        [0],
        [0],
        GRID_EVENT_IDS,
        DAY_COLUMN_IDS,
        0,
        1024,
        [],
        None,
    )
    outputs = _unpack_modal_outputs(result)
    assert outputs["modal_class"] == "modal show"
    assert outputs["form_children"] is not no_update
    assert outputs["footer_open"] is False
    assert outputs["close_timer_disabled"] is True
    assert outputs["day_modal_style"] == {"display": "none"}


@pytest.mark.usefixtures("casino")
def test_show_event_modal_allows_zero_click_value(monkeypatch, casino):
    callback = _event_modal_callback(casino)
    trigger_key = json.dumps({"type": "grid-event", "index": 0}, separators=(",", ":"))
    ctx = DummyCtx(
        {"type": "grid-event", "index": 0},
        value=0,
        states={f"{trigger_key}.n_clicks_timestamp": 1234},
    )
    monkeypatch.setattr("dash.callback_context", ctx, raising=False)

    result = callback(
        None,
        0,
        0,
        0,
        [0],
        [None],
        [1234],
        [None],
        [0],
        GRID_EVENT_IDS,
        DAY_COLUMN_IDS,
        0,
        1024,
        [],
        None,
    )
    outputs = _unpack_modal_outputs(result)
    assert outputs["modal_class"] == "modal show"


@pytest.mark.usefixtures("casino")
def test_show_event_modal_uses_state_when_context_missing(monkeypatch, casino):
    callback = _event_modal_callback(casino)
    ctx = DummyCtx({"type": "grid-event", "index": 0}, value=None)
    monkeypatch.setattr("dash.callback_context", ctx, raising=False)

    result = callback(
        None,
        0,
        0,
        0,
        [1],
        [0],
        [7890],
        [0],
        [0],
        GRID_EVENT_IDS,
        DAY_COLUMN_IDS,
        0,
        1024,
        [],
        None,
    )

    outputs = _unpack_modal_outputs(result)
    assert outputs["modal_class"] == "modal show"


@pytest.mark.usefixtures("casino")
def test_show_event_modal_zero_click_without_timestamp(monkeypatch, casino):
    callback = _event_modal_callback(casino)
    ctx = DummyCtx({"type": "grid-event", "index": 0}, value=0)
    monkeypatch.setattr("dash.callback_context", ctx, raising=False)

    with pytest.raises(dash.exceptions.PreventUpdate):
        callback(
            None,
            0,
            0,
            0,
            [0],
            [0],
            [0],
            [0],
            [0],
            GRID_EVENT_IDS,
            DAY_COLUMN_IDS,
            0,
            1024,
            [],
            None,
        )


@pytest.mark.usefixtures("casino")
def test_show_event_modal_none_click_value_prevents_update(monkeypatch, casino):
    callback = _event_modal_callback(casino)
    ctx = DummyCtx({"type": "grid-event", "index": 0}, value=None)
    monkeypatch.setattr("dash.callback_context", ctx, raising=False)

    with pytest.raises(dash.exceptions.PreventUpdate):
        callback(
            None,
            0,
            0,
            0,
            [0],
            [0],
            [None],
            [0],
            [0],
            GRID_EVENT_IDS,
            DAY_COLUMN_IDS,
            0,
            1024,
            [],
            None,
        )


@pytest.mark.usefixtures("casino")
def test_show_event_modal_close(monkeypatch, casino):
    callback = _event_modal_callback(casino)
    monkeypatch.setattr("dash.callback_context", DummyCtx("close-modal"), raising=False)

    result = callback(
        None,
        1,
        0,
        0,
        [0],
        [0],
        [0],
        [0],
        [0],
        GRID_EVENT_IDS,
        DAY_COLUMN_IDS,
        0,
        1024,
        [],
        None,
    )
    outputs = _unpack_modal_outputs(result)
    assert outputs["modal_class"] == "modal closing"
    assert outputs["close_timer_n"] == 0
    assert outputs["close_timer_disabled"] is False


@pytest.mark.usefixtures("casino")
def test_close_timer_ignores_reopened_modal(monkeypatch, casino):
    callback = _event_modal_callback(casino)
    monkeypatch.setattr("dash.callback_context", TimerCtx(), raising=False)

    result = callback(
        None,
        1,
        1,
        0,
        [0],
        [0],
        [0],
        [0],
        [0],
        GRID_EVENT_IDS,
        DAY_COLUMN_IDS,
        0,
        1024,
        [],
        "modal show",
    )
    outputs = _unpack_modal_outputs(result)
    assert outputs["modal_style"] is no_update
    assert outputs["modal_class"] is no_update
    assert outputs["modal_body"] is no_update
    assert outputs["close_timer_n"] == 0
    assert outputs["close_timer_disabled"] is True


@pytest.mark.usefixtures("casino")
def test_day_column_allows_zero_click_value(monkeypatch, casino):
    callback = _event_modal_callback(casino)
    trigger_key = json.dumps(
        {"type": "day-column", "index": "2025-07-12"}, separators=(",", ":")
    )
    ctx = DummyCtx(
        {"type": "day-column", "index": "2025-07-12"},
        value=0,
        states={f"{trigger_key}.n_clicks_timestamp": 4567},
    )
    monkeypatch.setattr("dash.callback_context", ctx, raising=False)

    result = callback(
        None,
        0,
        0,
        0,
        [0],
        [0],
        [0],
        [0],
        [4567],
        GRID_EVENT_IDS,
        DAY_COLUMN_IDS,
        0,
        1024,
        [],
        None,
    )
    outputs = _unpack_modal_outputs(result)
    assert outputs["day_modal_class"] == "modal show"


@pytest.mark.usefixtures("casino")
def test_day_column_none_click_value_prevents_update(monkeypatch, casino):
    callback = _event_modal_callback(casino)
    ctx = DummyCtx({"type": "day-column", "index": "2025-07-12"}, value=None)
    monkeypatch.setattr("dash.callback_context", ctx, raising=False)

    with pytest.raises(dash.exceptions.PreventUpdate):
        callback(
            None,
            0,
            0,
            0,
            [0],
            [0],
            [0],
            [0],
            [None],
            GRID_EVENT_IDS,
            DAY_COLUMN_IDS,
            0,
            1024,
            [],
            None,
        )


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
