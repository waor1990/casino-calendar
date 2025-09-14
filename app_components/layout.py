import plotly.graph_objs as go
from dash import dcc, html
from utils.colors import get_color

from .logging_config import setup_logger

# Initialize module logger
logger = setup_logger(__name__)

LEGEND_CASINOS: list[str] = []


def create_layout(app, df):
    logger.info("Creating application layout")
    logger.debug(f"Creating layout for {len(df)} events")

    try:
        layout = html.Div(
            className="main-layout",
            children=[
                dcc.Location(id="home-url", refresh=True),
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
                                        className=(
                                            "week-gap section-margin calendar-content"
                                        ),
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
                dcc.Store(id="last-day-date", data=None),
                dcc.Store(id="reopen-day-on-close", data=False),
                dcc.Store(id="theme-store", data="light", storage_type="local"),
                html.Div(id="theme-dummy", style={"display": "none"}),
                html.Div(id="animation-dummy", style={"display": "none"}),
                # Interval Triggers
                dcc.Interval(id="initial-trigger", interval=1, max_intervals=1),
                dcc.Interval(
                    id="close-timer", interval=600, n_intervals=0, max_intervals=0
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
                                html.Div(
                                    id="event-modal-body", className="base-padding"
                                ),
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
                                                                    margin=dict(
                                                                        l=0,
                                                                        r=0,
                                                                        t=0,
                                                                        b=0,
                                                                    ),
                                                                    height=10,
                                                                    plot_bgcolor="rgba(0,0,0,0)",
                                                                    paper_bgcolor="rgba(0,0,0,0)",
                                                                ),
                                                            ),
                                                            config={
                                                                "displayModeBar": False
                                                            },
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
                                html.Button(
                                    "Close",
                                    id="close-day-modal",
                                    className="modal-close",
                                ),
                            ],
                        )
                    ],
                ),
            ],
        )

        logger.info("Application layout created successfully")
        return layout

    except Exception as e:
        logger.error(f"Error creating layout: {e}", exc_info=True)
        raise


def sticky_header(df):
    logger.debug("Creating sticky header component")
    return html.Div(
        [
            html.H1(
                [
                    html.Button(
                        "🎰 Casino Event Calendar 📅",
                        id="home-button",
                        n_clicks=0,
                        className="calendar-title-home-button",
                        title="Home",
                    ),
                    html.Button(
                        "🌙",
                        id="theme-toggle",
                        n_clicks=0,
                        className="emoji-button theme-toggle",
                        title="Toggle dark mode",
                    ),
                ],
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
                            dcc.Dropdown(
                                id="event-type-filter",
                                options=[
                                    {"label": t, "value": t}
                                    for t in sorted(df["OfferType"].dropna().unique())
                                ],
                                multi=True,
                                placeholder="Filter by event type",
                                className="event-type-dropdown",
                                value=[],
                            ),
                            # Hotel booking link that appears when a casino is selected
                            html.Div(
                                id="hotel-booking-container",
                                style={
                                    "display": "none",
                                    "textAlign": "center",
                                    "marginTop": "10px",
                                },
                                children=[],
                            ),
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
                        ],
                        style={"display": "flex", "gap": "0.5rem"},
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "paddingBottom": "10px",
                    "--slide-distance": "8rem",
                },
            ),
            # Week Label and dynamic day headers
            html.Div(id="week-label", className="fade-text week-label", children=""),
            html.Div(id="day-label-row", className="day-label-wrapper"),
        ],
        className="sticky-header",
    )


def create_legend(df):
    logger.debug("Creating casino legend")
    legend_items = []
    LEGEND_CASINOS.clear()

    try:
        colors = get_color()
        unique_casinos = df["Casino"].unique()
        logger.debug(f"Found {len(unique_casinos)} unique casinos in data")

        for casino, color in colors.items():
            if casino in unique_casinos:
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

        logger.info(f"Created legend with {len(legend_items)} casino items")
        return legend_items

    except Exception as e:
        logger.error(f"Error creating legend: {e}", exc_info=True)
        return []
