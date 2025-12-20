"""Modal component factories for day, event, and casino index views."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import plotly.graph_objs as go  # type: ignore[import-untyped]
from dash import dcc, html

from casino_calendar.services.casino_index import load_casino_index
from casino_calendar.services.colors import get_color

DAY_MODAL_FOOTNOTE_TEXT = (
    "Only events that overlap the selected date (+/- 2 days) are shown. "
    "Events that span the entire week remain in the weekly grid. "
)

_DEFAULT_CASINO_COLORS: dict[str, dict[str, str]] = {
    "Muckleshoot Casino": {"bg": "#1e1c29", "bg_dark": "#a6a1c1"},
    "Tulalip Resort Casino": {"bg": "#155e6d", "bg_dark": "#2c94aa"},
}


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
                                    html.P(
                                        DAY_MODAL_FOOTNOTE_TEXT,
                                        className="day-modal-footnote",
                                        role="note",
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
    ordered_fields: list[tuple[str, Any]] = [(field, casino.get(field)) for field in known_fields if field in casino]
    ordered_fields.extend(
        (field, value) for field, value in casino.items() if field not in reserved_fields and field not in known_fields
    )

    casino_name = casino.get("name", "Unknown Casino")
    palette = get_color()
    palette_entry: dict[str, str] = palette.get(casino_name, {})
    fallback_colors: dict[str, str] = _DEFAULT_CASINO_COLORS.get(casino_name, {})
    bg_color: str | None = casino.get("color") or palette_entry.get("bg") or fallback_colors.get("bg")
    bg_dark_color: str | None = palette_entry.get("bg_dark") or fallback_colors.get("bg_dark")
    entry_style: dict[str, str] = {}
    if bg_color:
        entry_style["--bg"] = bg_color
    if bg_dark_color:
        entry_style["--bg-dark"] = bg_dark_color
    elif bg_color:
        entry_style["--bg-dark"] = bg_color
    today_label = datetime.now().strftime("%A")
    today_label_lower = today_label.lower()

    field_children = [
        html.Div(
            className="casino-index-field",
            children=[
                html.Span(f"{field.title()}:", className="casino-index-label"),
                html.Span(_format_casino_field_value(field, value, today_label, today_label_lower)),
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
        style=entry_style,
        children=[
            html.Div(casino_name, className="casino-index-name"),
            html.Div(field_children, className="casino-index-fields"),
        ],
    )


def _format_casino_field_value(field: str, value: Any, today_label: str, today_label_lower: str) -> Any:
    """Format casino index field values with special handling for hours."""

    if value in (None, ""):
        return "Not provided"

    if field.lower() in {"website", "player portal", "tax docs portal"}:
        return _format_casino_link(value)

    if field == "hours":
        formatted_hours = _format_hours_value(value, today_label, today_label_lower)
        return formatted_hours if formatted_hours is not None else "Not provided"

    return str(value)


def _format_casino_link(value: Any) -> Any:
    """Return a clickable link for casino URLs with a shortened label."""

    if value in (None, ""):
        return "Not provided"

    if not isinstance(value, str):
        return str(value)

    href = value.strip()
    parsed = urlparse(href)
    if not parsed.scheme:
        href = f"https://{href}"
        parsed = urlparse(href)

    host = parsed.netloc or parsed.path.split("/")[0] or href
    display_host = host if host.startswith("www.") else f"www.{host}"
    path = parsed.path.rstrip("/")
    display = display_host if not path or path == "/" else f"{display_host}{path}"

    max_length = 40
    if len(display) > max_length:
        if path and len(host) < max_length - 3:
            remaining = max_length - len(host) - 3
            trimmed_path = path[:remaining]
            display = f"{display_host}{trimmed_path}..."
        else:
            display = f"{display[: max_length - 3]}..."

    return html.A(display, href=href, target="_blank", rel="noopener noreferrer")


def _format_hours_value(hours: Any, today_label: str, today_label_lower: str) -> str | None:
    """Return hours for the current weekday when present.

    Supports dictionaries keyed by weekday names as well as multiline
    strings where each line begins with a weekday label (e.g. "Mon:" or
    "Monday -"). Falls back to the original value when a specific match is
    not found so existing free-form hours strings render intact.
    """

    if hours in (None, ""):
        return None

    candidates = {
        today_label,
        today_label[:3],
        today_label.upper(),
        today_label_lower,
        today_label[:3].upper(),
        today_label[:3].lower(),
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
