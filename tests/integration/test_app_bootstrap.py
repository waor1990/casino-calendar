"""Integration tests for the Dash application bootstrap."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from casino_calendar.dash_app import create_dash_app
from casino_calendar.dash_app.data import APIEventRepository
from casino_calendar.dash_app.services.layout_state import to_naive_utc


def _sample_events():
    return pd.DataFrame(
        {
            "EventName": ["Sample Event"],
            "Casino": ["ilani"],
            "Location": ["Main Hall"],
            "Offer": ["Free Play"],
            "OfferType": ["Free-Play"],
            "StartDate": [to_naive_utc(datetime(2025, 4, 14, 10))],
            "EndDate": [to_naive_utc(datetime(2025, 4, 14, 12))],
        }
    )


def test_create_dash_app_initializes_dash(monkeypatch):
    monkeypatch.setattr(APIEventRepository, "get_events", lambda self: _sample_events())

    app, server = create_dash_app()

    assert server is app.server
    assert app.title == "Casino Events Calendar"
    assert callable(app.layout)
    assert app.callback_map, "callbacks should be registered"
