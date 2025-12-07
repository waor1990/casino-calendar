"""Helpers for building and persisting event editing form state via REST API."""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
from casino_calendar.logging.config import setup_logger
from dash import dcc, html

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

    details = html.Div(
        build_event_info_rows([(str(k), v) for k, v in row.items()]),
        className="event-details",
    )

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
                                type="text"
                                if field["component"] == "input"
                                else "datetime-local",
                                className="event-edit-input",
                            )
                        ),
                    ],
                    className="event-edit-field",
                )
                for field in FORM_FIELDS
            ],
            className="event-edit-form",
        ),
    ]

    form_component = html.Div(form_children, id="event-edit-form-container")

    return [details], form_component


__all__ = ["build_form_defaults", "build_event_modal_children", "FORM_FIELDS"]
