"""Helpers for building and persisting event editing form state."""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
from dash import dcc, html

from casino_calendar.logging.config import setup_logger

from .layout_state import build_event_info_rows, to_naive_utc, to_pdt

logger = setup_logger(__name__)

FORM_FIELDS: list[dict[str, str]] = [
    {"key": "EventName", "label": "Event Name", "component": "input"},
    {"key": "OfferType", "label": "Offer Type", "component": "input"},
    {"key": "Offer", "label": "Offer Details", "component": "textarea"},
    {"key": "StartDate", "label": "Start Date", "component": "datetime"},
    {"key": "EndDate", "label": "End Date", "component": "datetime"},
]


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if pd.isna(value):  # type: ignore[arg-type]
        return ""
    return str(value)


def _format_timestamp_for_form(value: Any) -> str:
    if value is None:
        return ""
    try:
        ts = pd.to_datetime(value)
    except Exception:  # pragma: no cover - defensive
        logger.debug("Unable to parse timestamp value %s", value)
        return ""
    if pd.isna(ts):
        return ""
    return to_pdt(ts.to_pydatetime()).strftime("%Y-%m-%dT%H:%M")


def build_form_defaults(row: pd.Series) -> dict[str, str]:
    """Return default form values derived from ``row``."""

    defaults: dict[str, str] = {}
    for field in FORM_FIELDS:
        key = field["key"]
        if key in {"StartDate", "EndDate"}:
            defaults[key] = _format_timestamp_for_form(row.get(key))
        else:
            defaults[key] = _clean_string(row.get(key))
    return defaults


def build_event_modal_children(
    row: pd.Series, form_values: Mapping[str, Any] | None
) -> tuple[list[Any], html.Div]:
    """Return modal body content and a separate editable form container."""

    details = html.Div(build_event_info_rows(row.items()), className="event-details")

    defaults = build_form_defaults(row)
    if form_values:
        defaults.update({k: _clean_string(v) for k, v in form_values.items()})

    form_children: list[Any] = [
        html.Div(
            "Use the picker to select dates and 24-hour times.",
            className="event-edit-notice",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            field["label"],
                            className="event-edit-label",
                            htmlFor=f"event-edit-{field['key'].lower()}",
                        ),
                        html.Span(":", className="event-edit-separator"),
                        (
                            dcc.Textarea(
                                id=f"event-edit-{field['key'].lower()}",
                                value=defaults.get(field["key"], ""),
                                className="event-edit-input",
                                rows=4,
                            )
                            if field["component"] == "textarea"
                            else dcc.Input(
                                id=f"event-edit-{field['key'].lower()}",
                                value=defaults.get(field["key"], ""),
                                type=(
                                    "datetime-local"
                                    if field["component"] == "datetime"
                                    else "text"
                                ),
                                className="event-edit-input",
                                **(
                                    {"step": "60"}
                                    if field["component"] == "datetime"
                                    else {}
                                ),
                            )
                        ),
                    ],
                    className="event-edit-field",
                )
                for field in FORM_FIELDS
            ],
            className="event-edit-grid",
        ),
    ]

    form_container = html.Div(form_children, className="event-edit-form")
    body_children: list[Any] = [details]

    return body_children, form_container


def normalize_event_update(
    form_values: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Return normalized update mapping and list of validation errors."""

    normalized: dict[str, Any] = {}
    errors: list[str] = []

    required_fields = {"EventName", "StartDate", "EndDate"}

    for field in FORM_FIELDS:
        key = field["key"]
        raw_value = _clean_string(form_values.get(key))
        if key in required_fields and not raw_value:
            errors.append(f"{field['label']} is required.")
            continue

        if key in {"StartDate", "EndDate"}:
            if not raw_value:
                continue
            parsed = pd.to_datetime(raw_value, errors="coerce")
            if pd.isna(parsed):
                errors.append(f"{field['label']} must be a valid date and time.")
                continue
            normalized[key] = to_naive_utc(parsed.to_pydatetime())
        else:
            normalized[key] = raw_value

    return normalized, errors


__all__ = [
    "build_event_modal_children",
    "build_form_defaults",
    "normalize_event_update",
]
