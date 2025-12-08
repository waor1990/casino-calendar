"""Helpers for building and persisting event editing form state via REST API."""

from __future__ import annotations

from typing import Any, Mapping, cast

import pandas as pd
from casino_calendar.logging.config import setup_logger
from dash import dcc, html

from .layout_state import build_event_info_rows, to_pdt

logger = setup_logger(__name__)

# Available offer types that can be selected in the dropdown
OFFER_TYPE_OPTIONS = [
    "Free-Play",
    "Hospitality-Rewards",
    "Point-Based",
    "Giveaway",
    "Special-Events",
    "Offer",
]

FORM_FIELDS: list[dict[str, Any]] = [
    {"key": "EventName", "label": "Event Name", "component": "input"},
    {"key": "OfferType", "label": "Offer Type", "component": "dropdown"},
    {"key": "Offer", "label": "Offer Details", "component": "textarea"},
    {"key": "StartDate", "label": "Start Date", "component": "date_picker"},
    {"key": "EndDate", "label": "End Date", "component": "date_picker"},
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
    """Format timestamp as ISO 8601 date-time string (YYYY-MM-DDTHH:MM) for datetime-local input."""
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


def _format_timestamp_for_date_picker(value: Any) -> str:
    """Format timestamp as ISO 8601 date string (YYYY-MM-DD) for date picker."""
    if value is None:
        return ""
    try:
        ts = pd.to_datetime(value)
    except Exception:  # pragma: no cover - defensive
        logger.debug("Unable to parse timestamp value %s", value)
        return ""
    if pd.isna(ts):
        return ""
    return to_pdt(ts.to_pydatetime()).strftime("%Y-%m-%d")


def _format_timestamp_for_time_picker(value: Any) -> str:
    """Format timestamp as time string (HH:MM) for time input."""
    if value is None:
        return ""
    try:
        ts = pd.to_datetime(value)
    except Exception:  # pragma: no cover - defensive
        logger.debug("Unable to parse timestamp value %s", value)
        return ""
    if pd.isna(ts):
        return ""
    return to_pdt(ts.to_pydatetime()).strftime("%H:%M")


def build_form_defaults(row: pd.Series) -> dict[str, str]:
    """Return default form values derived from ``row``."""

    defaults: dict[str, str] = {}
    for field in FORM_FIELDS:
        key = field["key"]
        if key in {"StartDate", "EndDate"}:
            # Store as dict with date and time separately for date picker
            defaults[f"{key}_date"] = _format_timestamp_for_date_picker(row.get(key))
            defaults[f"{key}_time"] = _format_timestamp_for_time_picker(row.get(key))
        else:
            defaults[key] = _clean_string(row.get(key))
    return defaults


def build_event_modal_children(
    row: pd.Series, form_values: Mapping[str, Any] | None
) -> tuple[list[Any], html.Div]:
    """Return modal body content and a separate editable form container."""

    details = html.Div(
        build_event_info_rows([(str(k), v) for k, v in row.items()]),
        className="event-details",
    )

    defaults = build_form_defaults(row)
    if form_values:
        for key, value in form_values.items():
            if key not in {
                "StartDate_date",
                "StartDate_time",
                "EndDate_date",
                "EndDate_time",
            }:
                defaults[key] = _clean_string(value)

    form_children: list[Any] = [
        html.Div(
            "Use the picker to select dates and 24-hour times.",
            className="event-edit-notice",
        ),
        html.Div(
            [
                (
                    # Offer Type dropdown field
                    html.Div(
                        [
                            html.Label(
                                "Offer Type",
                                className="event-edit-label",
                                htmlFor="event-edit-offertype",
                            ),
                            html.Span(":", className="event-edit-separator"),
                            dcc.Dropdown(
                                id="event-edit-offertype",
                                options=[  # type: ignore[arg-type]
                                    {"label": opt, "value": opt}
                                    for opt in OFFER_TYPE_OPTIONS
                                ],
                                value=defaults.get("OfferType", ""),
                                className="event-edit-input event-edit-dropdown",
                                clearable=False,
                            ),
                        ],
                        className="event-edit-field",
                    )
                    if field["key"] == "OfferType"
                    else (
                        # Date picker with time field
                        html.Div(
                            [
                                html.Label(
                                    field["label"],
                                    className="event-edit-label",
                                    htmlFor=f"event-edit-{field['key'].lower()}-date",
                                ),
                                html.Span(":", className="event-edit-separator"),
                                html.Div(
                                    [
                                        dcc.DatePickerSingle(
                                            id=f"event-edit-{field['key'].lower()}-date",
                                            date=defaults.get(
                                                f"{field['key']}_date", ""
                                            ),
                                            className="event-edit-date-picker",
                                            display_format="YYYY-MM-DD",
                                        ),
                                        dcc.Input(
                                            id=f"event-edit-{field['key'].lower()}-time",
                                            type=cast(Any, "time"),
                                            value=defaults.get(
                                                f"{field['key']}_time", ""
                                            ),
                                            className="event-edit-time-input",
                                        ),
                                    ],
                                    className="event-edit-datetime-wrapper",
                                ),
                            ],
                            className="event-edit-field event-edit-datetime-field",
                        )
                        if field["component"] == "date_picker"
                        else (
                            # Textarea field
                            html.Div(
                                [
                                    html.Label(
                                        field["label"],
                                        className="event-edit-label",
                                        htmlFor=f"event-edit-{field['key'].lower()}",
                                    ),
                                    html.Span(":", className="event-edit-separator"),
                                    dcc.Textarea(
                                        id=f"event-edit-{field['key'].lower()}",
                                        value=defaults.get(field["key"], ""),
                                        className="event-edit-input",
                                        rows=4,
                                    ),
                                ],
                                className="event-edit-field",
                            )
                            if field["component"] == "textarea"
                            else (
                                # Regular input field
                                html.Div(
                                    [
                                        html.Label(
                                            field["label"],
                                            className="event-edit-label",
                                            htmlFor=f"event-edit-{field['key'].lower()}",
                                        ),
                                        html.Span(
                                            ":", className="event-edit-separator"
                                        ),
                                        dcc.Input(
                                            id=f"event-edit-{field['key'].lower()}",
                                            value=defaults.get(field["key"], ""),
                                            type="text",
                                            className="event-edit-input",
                                        ),
                                    ],
                                    className="event-edit-field",
                                )
                            )
                        )
                    )
                )
                for field in FORM_FIELDS
            ],
            className="event-edit-form",
        ),
    ]

    # Return the modal details and a single Div wrapper for the editable form
    return [details], html.Div(form_children, className="event-edit-form-container")


__all__ = ["build_form_defaults", "build_event_modal_children", "FORM_FIELDS"]
