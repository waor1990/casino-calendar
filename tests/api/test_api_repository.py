from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import pytest
import requests

from casino_calendar.dash_app.data.api_repository import APIEventRepository


class DummyResponse:
    def __init__(self, payload: Any, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.content = b"{}" if payload is not None else b""

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> Any:  # pragma: no cover - simple passthrough
        return self._payload


def test_get_events_returns_normalized_dataframe(monkeypatch):
    payload = [
        {
            "EventID": "123",
            "EventName": "API Event",
            "Offer": "Free Play",
            "StartDate": "2025-12-01T20:00:00Z",
            "EndDate": "2025-12-01T21:00:00Z",
            "Casino": "Luxor",
            "Location": "Las Vegas",
        }
    ]

    def fake_request(method: str, url: str, timeout: int = 10, **kwargs: Any):
        assert method == "get"
        assert url.endswith("/events")
        return DummyResponse(payload)

    monkeypatch.setattr("requests.request", fake_request)

    repo = APIEventRepository(base_url="http://api.test")
    df = repo.get_events()

    assert isinstance(df, pd.DataFrame)
    assert df.loc[0, "EventID"] == "123"
    assert isinstance(df.loc[0, "StartDate"], pd.Timestamp)
    assert df.loc[0, "StartDate"].tzinfo is None


def test_save_event_raises_for_http_error(monkeypatch):
    def fake_request(method: str, url: str, timeout: int = 10, **kwargs: Any):
        return DummyResponse({}, status_code=500)

    monkeypatch.setattr("requests.request", fake_request)

    repo = APIEventRepository(base_url="http://api.test")

    with pytest.raises(requests.HTTPError):
        repo.save_event(
            {
                "EventName": "Broken Event",
                "Offer": "",
                "StartDate": datetime.utcnow().isoformat() + "Z",
                "EndDate": datetime.utcnow().isoformat() + "Z",
                "Casino": "Luxor",
                "Location": "Las Vegas",
            }
        )


def test_update_event_uses_put(monkeypatch):
    captured: dict[str, Any] = {}

    def fake_request(method: str, url: str, timeout: int = 10, **kwargs: Any):
        captured.update({"method": method, "url": url, "kwargs": kwargs})
        return DummyResponse({"EventID": "abc"})

    monkeypatch.setattr("requests.request", fake_request)

    repo = APIEventRepository(base_url="http://api.test")
    repo.update_event("abc", {"EventName": "Updated"})

    assert captured["method"] == "put"
    assert captured["url"].endswith("/events/abc")
    assert "json" in captured["kwargs"]
