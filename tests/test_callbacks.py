from datetime import datetime

import pandas as pd
import pytest
from app_components.callbacks import register_callbacks
from app_components.utils import to_naive_utc
from dash import Dash
from freezegun import freeze_time


class DummyCtx:
    def __init__(self, triggered_id):
        self.triggered_id = triggered_id
        self.triggered = [{"prop_id": f"{triggered_id}.n_clicks", "value": 1}]


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
    func = app.callback_map[
        (
            "..week-offset.data...prev-button.disabled...next-button.disabled..."
            "next-button.title.."
        )
    ]["callback"].__wrapped__

    monkeypatch.setattr("dash.callback_context", DummyCtx("next-button"), raising=False)
    offset, prev_disabled, next_disabled, title = func(0, 1, 0)
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
    func = app.callback_map[
        (
            "..week-offset.data...prev-button.disabled...next-button.disabled..."
            "next-button.title.."
        )
    ]["callback"].__wrapped__

    monkeypatch.setattr("dash.callback_context", DummyCtx("next-button"), raising=False)
    offset, _, next_disabled, _ = func(0, 1, 0)
    assert offset == 0
    assert next_disabled


@pytest.mark.usefixtures("casino")
def test_toggle_overflow(monkeypatch, casino):
    df = pd.DataFrame()
    app = Dash(__name__)
    register_callbacks(app, df)
    func = app.callback_map["..overflow-box.className...overflow-toggle.children.."][
        "callback"
    ].__wrapped__

    result = func(1, "2025-04-13")
    assert result[0] == "overflow-box-expand show"
    assert "Hide" in result[1]


@pytest.mark.usefixtures("casino")
def test_toggle_casino_filter(monkeypatch, casino):
    df = pd.DataFrame({"EventName": ["E1"], "Casino": [casino]})
    app = Dash(__name__)
    register_callbacks(app, df)
    func = app.callback_map["selected-casinos.data"]["callback"].__wrapped__

    monkeypatch.setattr(
        "dash.callback_context",
        DummyCtx({"type": "casino-filter", "index": casino}),
        raising=False,
    )

    result = func([1], [{"type": "casino-filter", "index": casino}], [])
    assert result == [casino]


@pytest.mark.usefixtures("casino")
def test_hotel_booking_link_display(casino):
    """Test hotel booking link display logic."""
    df = pd.DataFrame({"EventName": ["E1"], "Casino": [casino]})
    app = Dash(__name__)
    register_callbacks(app, df)
    func = app.callback_map[
        "..hotel-booking-container.children...hotel-booking-container.style.."
    ]["callback"].__wrapped__

    # Test with no casino selected
    children, style = func([])
    assert children == []
    assert style["display"] == "none"

    # Test with multiple casinos selected
    children, style = func([casino, "Another Casino"])
    assert children == []
    assert style["display"] == "none"

    # Test with a casino that has a booking URL
    # Mock the configuration cache to return booking sites data
    from utils import config_cache

    original_get_config = config_cache.get_config

    def mock_get_config(filename):
        if filename == "hotel_book_sites.json":
            return {casino: "https://example.com/booking"}
        return original_get_config(filename)

    config_cache.get_config = mock_get_config

    try:
        children, style = func([casino])
        assert len(children) == 1
        assert style["display"] == "block"
        assert children[0].href == "https://example.com/booking"
        assert "Hotel Booking" in children[0].children
    finally:
        # Restore original get_config function
        config_cache.get_config = original_get_config

    # Test with a casino that has N/A booking URL
    def mock_get_config_na(filename):
        if filename == "hotel_book_sites.json":
            return {casino: "N/A"}
        return original_get_config(filename)

    config_cache.get_config = mock_get_config_na

    try:
        children, style = func([casino])
        assert children == []
        assert style["display"] == "none"
    finally:
        # Restore original get_config function
        config_cache.get_config = original_get_config
