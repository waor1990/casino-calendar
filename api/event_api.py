"""Lightweight REST API for managing Casino Calendar events."""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from casino_calendar.dash_app.data.transforms import categorize_offer_type  # noqa: E402
from casino_calendar.logging.config import setup_logger  # noqa: E402
from casino_calendar.settings import DATA_DIR  # noqa: E402

logger = setup_logger(__name__)

EVENTS_FILE = DATA_DIR / "events.json"
REQUIRED_FIELDS = [
    "EventName",
    "Offer",
    "StartDate",
    "EndDate",
    "Casino",
    "Location",
]


def load_events(events_path: Path = EVENTS_FILE) -> list[dict[str, Any]]:
    """Return events from ``events_path`` creating the file if needed."""

    events_path.parent.mkdir(parents=True, exist_ok=True)
    if not events_path.exists():
        logger.info("Creating new events store at %s", events_path)
        events_path.write_text("[]", encoding="utf-8")
        return []

    try:
        with events_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        logger.error("Failed to parse events file: %s", exc)
        raise


def save_events(events: list[dict[str, Any]], events_path: Path = EVENTS_FILE) -> None:
    """Persist ``events`` atomically to ``events_path``."""

    events_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = events_path.with_suffix(".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(events, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    temp_path.replace(events_path)
    logger.info("Saved %d event(s) to %s", len(events), events_path)


def _parse_iso8601(date_str: str) -> datetime:
    """Return parsed datetime for an ISO 8601 string ensuring UTC timezone."""

    if not isinstance(date_str, str):
        raise ValueError("Date fields must be strings")

    normalized = date_str.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("Date values must include a timezone")

    return parsed.astimezone(timezone.utc)


def _isoformat_utc(dt: datetime) -> str:
    """Return UTC ISO 8601 string with ``Z`` suffix."""

    return (
        dt.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _validate_event_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize incoming event payload values."""

    missing = [field for field in REQUIRED_FIELDS if not payload.get(field)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    start = _parse_iso8601(payload["StartDate"])
    end = _parse_iso8601(payload["EndDate"])
    if end < start:
        raise ValueError("EndDate must be after StartDate")

    event_name = str(payload.get("EventName", "")).strip()
    offer = str(payload.get("Offer", "")).strip()
    offer_type = payload.get("OfferType") or categorize_offer_type(event_name, offer)

    normalized = {
        "EventName": event_name,
        "OfferType": str(offer_type),
        "Offer": offer,
        "StartDate": _isoformat_utc(start),
        "EndDate": _isoformat_utc(end),
        "Casino": str(payload.get("Casino", "")).strip(),
        "Location": str(payload.get("Location", "")).strip(),
    }

    return normalized


def create_app(events_path: Path | None = None) -> Flask:
    """Return configured Flask application for the event API."""

    app = Flask(__name__)
    store_path = events_path or EVENTS_FILE

    @app.get("/events")
    def get_events():
        events = load_events(store_path)
        return jsonify(events), HTTPStatus.OK

    @app.post("/events")
    def create_event():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return (
                jsonify({"error": "Request body must be a JSON object"}),
                HTTPStatus.BAD_REQUEST,
            )

        try:
            event = _validate_event_payload(payload)
        except (ValueError, KeyError) as exc:
            logger.warning("Invalid event payload: %s", exc)
            return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

        event["EventID"] = str(uuid.uuid4())
        events = load_events(store_path)
        events.append(event)
        save_events(events, store_path)

        return jsonify(event), HTTPStatus.CREATED

    @app.put("/events/<event_id>")
    def update_event(event_id: str):
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return (
                jsonify({"error": "Request body must be a JSON object"}),
                HTTPStatus.BAD_REQUEST,
            )

        events = load_events(store_path)
        match_index = next(
            (
                idx
                for idx, event in enumerate(events)
                if event.get("EventID") == event_id
            ),
            None,
        )
        if match_index is None:
            return (
                jsonify({"error": f"Event with id {event_id} not found"}),
                HTTPStatus.NOT_FOUND,
            )

        try:
            updated_event = _validate_event_payload(payload)
        except (ValueError, KeyError) as exc:
            logger.warning("Invalid event payload: %s", exc)
            return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

        updated_event["EventID"] = event_id
        events[match_index] = updated_event
        save_events(events, store_path)

        return jsonify(updated_event), HTTPStatus.OK

    return app


if __name__ == "__main__":
    api_app = create_app()
    api_app.run(host="0.0.0.0", port=5001)
