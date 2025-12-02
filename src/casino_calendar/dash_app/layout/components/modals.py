"""Modal component factories for day, event, and casino index views."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import plotly.graph_objs as go
from casino_calendar.services.casino_index import load_casino_index
from dash import dcc, html


def build_event_modal() -> html.Div:
    """Return the hidden event modal container."""

    return html.Div(
        id="event-modal",
        className="modal",
        children=[
            html.Div(
                id="event-modal-content",
                className="modal-content",
                children=[
                    html.Div(id="event-modal-body", className="base-padding"),
                    html.Button("Close", id="close-modal", className="modal-close"),
                ],
            )
        ],
    )


def build_day_modal() -> html.Div:
    """Return the hidden day modal container and overlay graph."""

    return html.Div(
        id="day-modal",
        className="modal",
        children=[
            html.Div(
                id="day-modal-content",
                className="modal-content",
                children=[
                    html.Div(
                        id="day-modal-body",
                        children=[
                            html.Div(
                                id="day-modal-content-container",
                                className="base-padding",
                                children=[
                                    html.H2(
                                        id="day-modal-title",
                                        className="day-label day-modal-title",
                                    ),
                                    html.Div(
                                        id="day-grid-wrapper",
                                        style={"position": "relative"},
                                        children=[
                                            html.Div(id="day-grid-content"),
                                            dcc.Graph(
                                                id="day-event-catcher",
                                                className="day-event-catcher",
                                                figure=go.Figure(
                                                    data=[],
                                                    layout=go.Layout(
                                                        clickmode="event+select",
                                                        xaxis=dict(
                                                            visible=False,
                                                            range=[0, 1],
                                                            fixedrange=True,
                                                        ),
                                                        yaxis=dict(
                                                            visible=False,
                                                            range=[0, 1],
                                                            fixedrange=True,
                                                        ),
                                                        margin=dict(l=0, r=0, t=0, b=0),
                                                        height=10,
                                                        plot_bgcolor="rgba(0,0,0,0)",
                                                        paper_bgcolor="rgba(0,0,0,0)",
                                                    ),
                                                ),
                                                config={"displayModeBar": False},
                                                style={
                                                    "height": "0px",
                                                    "pointerEvents": "none",
                                                },
                                            ),
                                        ],
                                    ),
                                ],
                            )
                        ],
                    ),
                    html.Button("Close", id="close-day-modal", className="modal-close"),
                ],
            )
        ],
    )


def _build_casino_index_entry(casino: dict[str, Any]) -> html.Div:
    """Return a single casino entry for the casino index modal."""

    known_fields = ["address", "hours", "distance"]
    reserved_fields = {"name", "color"}
    ordered_fields: list[tuple[str, Any]] = [
        (field, casino.get(field)) for field in known_fields if field in casino
    ]
    ordered_fields.extend(
        (field, value)
        for field, value in casino.items()
        if field not in reserved_fields and field not in known_fields
    )

    casino_name = casino.get("name", "Unknown Casino")
    accent_color = casino.get("color")
    name_style: dict[str, str] = {"color": accent_color} if accent_color else {}

    field_children = [
        html.Div(
            className="casino-index-field",
            children=[
                html.Span(f"{field.title()}:", className="casino-index-label"),
                html.Span(
                    _format_field_value(field, value)
                    if value not in (None, "")
                    else "Not provided"
                ),
            ],
        )
        for field, value in ordered_fields
    ]

    if not field_children:
        field_children.append(
            html.Div(
                "No additional details provided.",
                className="casino-index-field muted-text",
            )
        )

    return html.Div(
        className="casino-index-entry",
        children=[
            html.Div(casino_name, className="casino-index-name", style=name_style),
            html.Div(field_children, className="casino-index-fields"),
        ],
    )


def _format_field_value(field: str, value: Any) -> str:
    """Return a formatted value for known casino index fields.

    The ``hours`` field is reduced to the current day's entry when the
    source value contains a weekly schedule; all other fields are coerced
    to strings unchanged.
    """

    if field == "hours":
        formatted_hours = _format_hours_value(value)
        if formatted_hours is not None:
            return formatted_hours
        return "Not provided"

    return str(value)


def _format_hours_value(hours: Any) -> str | None:
    """Return hours for the current weekday when present.

    Supports dictionaries keyed by weekday names as well as multiline
    strings where each line begins with a weekday label (e.g. "Mon:" or
    "Monday -"). Falls back to the original value when a specific match is
    not found so existing free-form hours strings render intact.
    """

    if hours in (None, ""):
        return None

    today = datetime.now().strftime("%A")
    candidates = {
        today,
        today[:3],
        today.upper(),
        today.lower(),
        today[:3].upper(),
        today[:3].lower(),
    }
    lowered_candidates = {c.lower() for c in candidates}

    if isinstance(hours, dict):
        for key, value in hours.items():
            if key in candidates or str(key).lower() in lowered_candidates:
                return str(value)
        return None

    if isinstance(hours, (list, tuple)):
        lines = [str(item) for item in hours]
    elif isinstance(hours, str):
        lines = [line.strip() for line in hours.splitlines() if line.strip()]
    else:
        return str(hours)

    for line in lines:
        lowered = line.lower()
        for candidate in lowered_candidates:
            if lowered.startswith(candidate):
                if ":" in line:
                    return line.split(":", 1)[1].strip()
                if "-" in line:
                    return line.split("-", 1)[1].strip()
                parts = line.split(None, 1)
                return parts[1].strip() if len(parts) > 1 else line.strip()

    return "\n".join(lines)


def build_casino_index_modal(
    casino_index: list[dict[str, Any]] | None = None,
) -> html.Div:
    """Return the casino index modal listing metadata for each casino.

    The modal renders entries from ``data/lookups/casino_index.json`` as a
    scrollable list, preserving any extra fields supplied in the lookup.
    """

    casino_entries = casino_index if casino_index is not None else load_casino_index()

    body_content = (
        html.Div(
            [_build_casino_index_entry(entry) for entry in casino_entries],
            className="casino-index-list",
        )
        if casino_entries
        else html.P("No casino index details available", className="muted-text")
    )

    return html.Div(
        id="casino-index-modal",
        className="modal",
        style={"display": "none"},
        children=[
            html.Div(
                id="casino-index-modal-content",
                className="modal-content",
                children=[
                    html.H2("Casino Index", className="modal-title"),
                    body_content,
                    html.Button(
                        "Close",
                        id="close-casino-index-modal",
                        className="modal-close",
                    ),
                ],
            )
        ],
    )


__all__ = ["build_casino_index_modal", "build_day_modal", "build_event_modal"]
