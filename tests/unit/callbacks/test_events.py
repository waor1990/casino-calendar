"""Unit tests for event oriented callbacks."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import pytest
from casino_calendar.dash_app.callbacks import register_callbacks
from casino_calendar.dash_app.services.layout_state import to_naive_utc
from dash import Dash


class DummyCtx:
    def __init__(self, triggered_id):
        self.triggered_id = triggered_id
        self.triggered = [{"prop_id": f"{triggered_id}.n_clicks", "value": 1}]


class ModalCtx:
    def __init__(self, triggered_id: Any):
        self.triggered_id = triggered_id
        self.triggered = [{"prop_id": f"{triggered_id}.n_clicks", "value": 1}]
        self.inputs_list: list[Any] = []
        self.states: dict[str, Any] = {}


def _get_callback_entry(app: Dash, target_id: str, target_property: str):
    for entry in app.callback_map.values():
        outputs = (
            entry["output"] if isinstance(entry["output"], list) else [entry["output"]]
        )
        for idx, output in enumerate(outputs):
            if (
                getattr(output, "component_id", None) == target_id
                and getattr(output, "component_property", None) == target_property
            ):
                return entry, outputs, idx
    raise AssertionError(
        f"Callback with output {target_id}.{target_property} not found"
    )


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


@pytest.mark.usefixtures("casino")
def test_event_modal_open_resets_footer(monkeypatch, casino):
    df = pd.DataFrame(
        {
            "EventName": ["E1"],
            "Casino": [casino],
            "Location": ["Main Hall"],
            "Offer": [""],
            "StartDate": [to_naive_utc(datetime(2025, 4, 14))],
            "EndDate": [to_naive_utc(datetime(2025, 4, 15))],
        }
    )

    app = Dash(__name__)
    register_callbacks(app, df)
    entry, outputs, _ = _get_callback_entry(app, "event-modal", "style")
    callback = entry["callback"].__wrapped__
    status_index = next(
        i
        for i, output in enumerate(outputs)
        if output.component_id == "event-save-status"
        and output.component_property == "children"
    )

    monkeypatch.setattr(
        "dash.callback_context",
        ModalCtx({"type": "grid-event", "index": 0}),
        raising=False,
    )

    result = callback(
        None,
        0,
        0,
        0,
        [1],
        [1],
        [],
        [1],
        [],
        [{"type": "grid-event", "index": 0}],
        [],
        0,
        1024,
        [],
        "",
    )

    assert result[status_index] == ""
    assert result[status_index + 1] == "event-save-status"


@pytest.mark.usefixtures("casino")
def test_event_modal_close_clears_footer(monkeypatch, casino):
    df = pd.DataFrame(
        {
            "EventName": ["E1"],
            "Casino": [casino],
            "Location": ["Main Hall"],
            "Offer": [""],
            "StartDate": [to_naive_utc(datetime(2025, 4, 14))],
            "EndDate": [to_naive_utc(datetime(2025, 4, 15))],
        }
    )

    app = Dash(__name__)
    register_callbacks(app, df)
    entry, outputs, _ = _get_callback_entry(app, "event-modal", "style")
    callback = entry["callback"].__wrapped__
    status_index = next(
        i
        for i, output in enumerate(outputs)
        if output.component_id == "event-save-status"
        and output.component_property == "children"
    )

    monkeypatch.setattr("dash.callback_context", ModalCtx("close-modal"), raising=False)

    result = callback(
        None,
        1,
        0,
        0,
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        0,
        1024,
        [],
        "modal show",
    )

    assert result[status_index] == ""
    assert result[status_index + 1] == "event-save-status"


@pytest.mark.usefixtures("casino")
def test_success_message_does_not_persist_between_modals(monkeypatch, casino):
    df = pd.DataFrame(
        {
            "EventName": ["E1", "E2"],
            "Casino": [casino, casino],
            "Location": ["Main Hall", "Side Hall"],
            "Offer": ["", ""],
            "StartDate": [
                to_naive_utc(datetime(2025, 4, 14)),
                to_naive_utc(datetime(2025, 4, 16)),
            ],
            "EndDate": [
                to_naive_utc(datetime(2025, 4, 15)),
                to_naive_utc(datetime(2025, 4, 17)),
            ],
        }
    )

    app = Dash(__name__)
    register_callbacks(app, df)

    save_entry, save_outputs, _ = _get_callback_entry(app, "event-data-refresh", "data")
    save_callback = save_entry["callback"].__wrapped__
    status_index = next(
        i
        for i, output in enumerate(save_outputs)
        if output.component_id == "event-save-status"
        and output.component_property == "children"
    )

    save_result = save_callback(
        1,
        {"index": 0},
        "Updated Event",
        "Promo",
        "Details",
        "2025-04-14T00:00",
        "2025-04-15T00:00",
    )

    assert save_result[status_index] == "Changes saved successfully."

    modal_entry, modal_outputs, _ = _get_callback_entry(app, "event-modal", "style")
    modal_callback = modal_entry["callback"].__wrapped__
    modal_status_index = next(
        i
        for i, output in enumerate(modal_outputs)
        if output.component_id == "event-save-status"
        and output.component_property == "children"
    )

    monkeypatch.setattr(
        "dash.callback_context",
        ModalCtx({"type": "grid-event", "index": 1}),
        raising=False,
    )

    modal_result = modal_callback(
        None,
        0,
        0,
        0,
        [0, 1],
        [10, 20],
        [],
        [10, 20],
        [],
        [
            {"type": "grid-event", "index": 0},
            {"type": "grid-event", "index": 1},
        ],
        [],
        0,
        1024,
        [],
        "",
    )

    assert modal_result[modal_status_index] == ""
    assert modal_result[modal_status_index + 1] == "event-save-status"
