"""Modal component factories for day, event, and casino index views."""

from __future__ import annotations

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
                html.Span(str(value) if value not in (None, "") else "Not provided"),
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
