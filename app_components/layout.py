import plotly.graph_objs as go
from dash import dcc, html

from utils.colors import get_color

LEGEND_CASINOS: list[str] = []


def create_layout(app, df):
    return html.Div(
        className="main-layout",
        children=[
            # Header section only (wrapped for height calc)
            html.Div(
                id="app-header",
                children=[
                    sticky_header(df),
                    # Scrollable Calendar Body
                    html.Div(
                        id="calendar-scroll-body",
                        className="calendar-scroll-body",
                        children=[
                            # Main calendar area
                            dcc.Loading(
                                id="calendar-loading",
                                type="circle",
                                color="#6A5ACD",
                                children=html.Div(
                                    id="week-chart-container",
                                    className="week-gap section-margin calendar-content",
                                ),
                            ),
                        ],
                    ),
                ],
            ),
            # State Stores
            dcc.Store(id="usable-height", data=600),
            dcc.Store(id="screen-width", data=1024),
            dcc.Store(id="week-offset", data=0),
            dcc.Store(id="overflow-date"),
            dcc.Store(id="animation-refresh"),
            dcc.Store(id="selected-casinos", data=[]),
            html.Div(id="animation-dummy", style={"display": "none"}),
            # Interval Triggers
            dcc.Interval(id="initial-trigger", interval=1, max_intervals=1),
            dcc.Interval(
                id="close-timer", interval=600, n_intervals=0, max_intervals=0
            ),
            # Invisible catcher for click events
            dcc.Graph(
                id="day-event-catcher",
                figure=go.Figure(),
                style={
                    "visibility": "hidden",
                    "height": "0px",
                    "pointerEvents": "none",
                },
            ),
            # Event Modal Popup
            html.Div(
                id="event-modal",
                className="modal",
                children=[
                    html.Div(
                        id="event-modal-content",
                        className="modal-content",
                        children=[
                            html.Div(id="event-modal-body", className="base-padding"),
                            html.Button(
                                "Close", id="close-modal", className="modal-close"
                            ),
                        ],
                    )
                ],
            ),
            # Day Modal Popup
            html.Div(
                id="day-modal",
                className="modal",
                children=[
                    html.Div(
                        id="day-modal-content",
                        className="modal-content",
                        children=[
                            html.Div(
                                id="day-modal-body",
                                className="base-padding",
                            ),
                            html.Button(
                                "Close", id="close-day-modal", className="modal-close"
                            ),
                        ],
                    )
                ],
            ),
        ],
    )


def sticky_header(df):
    return html.Div(
        [
            html.H1(
                "🎰 Casino Event Calendar 📅",
                className="calendar-title",
            ),
            # Navigation & Legend
            html.Div(
                id="header-container",
                className="legend-container",
                children=[
                    html.Button(
                        "🎲",
                        id="prev-button",
                        title="Prior Week",
                        n_clicks=0,
                        className="emoji-button",
                    ),
                    html.Div(
                        [
                            html.Legend(
                                "Casino Legend:",
                                className="legend-title legend-gap",
                            ),
                            html.Div(create_legend(df), className="legend-container"),
                        ],
                        style={
                            "flex": "1",
                        },
                    ),
                    html.Div(
                        [
                            html.Button(
                                "🎰",
                                id="next-button",
                                n_clicks=0,
                                className="emoji-button",
                            ),
                            html.Button(
                                "🌙",
                                id="theme-toggle",
                                n_clicks=0,
                                className="emoji-button",
                                title="Toggle dark mode",
                            ),
                        ],
                        style={"display": "flex", "gap": "0.5rem"},
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "paddingBottom": "10px",
                },
            ),
            # Week Label and dynamic day headers
            html.Div(id="week-label", className="fade-text week-label", children=""),
            html.Div(id="day-label-row", className="day-label-wrapper"),
        ],
        className="sticky-header",
    )


def create_legend(df):
    legend_items = []
    LEGEND_CASINOS.clear()
    for casino, color in get_color().items():
        if casino in df["Casino"].unique():
            LEGEND_CASINOS.append(casino)
            legend_items.append(
                html.Button(
                    className="legend-item legend-button",
                    id={"type": "casino-filter", "index": casino},
                    n_clicks=0,
                    children=[
                        html.Div(
                            className="legend-color-box",
                            style={"backgroundColor": color["bg"]},
                        ),
                        html.Span(
                            f"{casino}",
                            className="legend-text legend-gap",
                            style={"color": color["bg"], "marginRight": "4px"},
                        ),
                    ],
                )
            )
    return legend_items
