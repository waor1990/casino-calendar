from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from api.event_api import create_app, load_events


@pytest.fixture()
def api_client(tmp_path: Path):
    events_path = tmp_path / "events.json"
    app = create_app(events_path=events_path)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client, events_path


def _sample_event(
    start: datetime | None = None, end: datetime | None = None
) -> dict[str, str]:
    start_dt = start or datetime(2025, 12, 1, 20, 0, tzinfo=timezone.utc)
    end_dt = end or datetime(2025, 12, 1, 23, 59, tzinfo=timezone.utc)
    return {
        "EventName": "Test Event",
        "OfferType": "Free-Play",
        "Offer": "Test Offer",
        "StartDate": start_dt.isoformat().replace("+00:00", "Z"),
        "EndDate": end_dt.isoformat().replace("+00:00", "Z"),
        "Casino": "Luxor",
        "Location": "Las Vegas",
    }


def test_get_returns_empty_list_and_creates_file(api_client):
    client, events_path = api_client

    response = client.get("/events")

    assert response.status_code == 200
    assert response.get_json() == []
    assert events_path.exists()


def test_post_persists_event(api_client):
    client, events_path = api_client
    payload = _sample_event()

    response = client.post("/events", json=payload)

    assert response.status_code == 201
    body = response.get_json()
    assert body["EventID"]
    assert body["StartDate"].endswith("Z")

    events_on_disk = json.loads(events_path.read_text(encoding="utf-8"))
    assert len(events_on_disk) == 1
    assert events_on_disk[0]["EventID"] == body["EventID"]


def test_post_rejects_invalid_dates(api_client):
    client, _ = api_client
    payload = _sample_event()
    payload["StartDate"] = "not-a-date"

    response = client.post("/events", json=payload)

    assert response.status_code == 400
    assert "Missing" not in response.get_json().get("error", "")


def test_put_updates_existing_event(api_client):
    client, events_path = api_client
    payload = _sample_event()

    created = client.post("/events", json=payload).get_json()
    payload["EventName"] = "Updated Event"

    update_response = client.put(f"/events/{created['EventID']}", json=payload)

    assert update_response.status_code == 200
    updated_body = update_response.get_json()
    assert updated_body["EventName"] == "Updated Event"

    events_on_disk = json.loads(events_path.read_text(encoding="utf-8"))
    assert events_on_disk[0]["EventName"] == "Updated Event"


def test_put_missing_event_returns_not_found(api_client):
    client, _ = api_client
    payload = _sample_event()

    response = client.put("/events/missing-id", json=payload)

    assert response.status_code == 404
    assert "not found" in response.get_json().get("error", "")


def test_load_events_handles_missing_file(tmp_path: Path):
    events_path = tmp_path / "events.json"

    events = load_events(events_path)

    assert events == []
    assert events_path.exists()
