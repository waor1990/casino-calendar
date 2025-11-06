"""Modal component factories for day and event detail views."""

from __future__ import annotations

import plotly.graph_objs as go
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
                    html.Div(
                        className="modal-footer",
                        children=[
                            html.Details(
                                id="event-edit-footer",
                                className="modal-footer-edit",
                                open=False,
                                children=[
                                    html.Summary(
                                        "Edit Event",
                                        className="modal-footer-summary",
                                    ),
                                    html.Div(
                                        className="modal-footer-panel",
                                        children=[
                                            html.Div(
                                                id="event-edit-form-container"
                                            ),
                                            html.Div(
                                                id="event-save-status",
                                                className="event-save-status",
                                            ),
                                            html.Div(
                                                className="modal-footer-buttons",
                                                children=[
                                                    html.Button(
                                                        "Save Changes",
                                                        id="event-save-button",
                                                        className="modal-save",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            html.Button(
                                "Close",
                                id="close-modal",
                                className="modal-close",
                            ),
                        ],
                    ),
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


__all__ = ["build_day_modal", "build_event_modal"]
