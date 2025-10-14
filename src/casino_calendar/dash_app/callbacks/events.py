import time
from datetime import datetime, timedelta
from typing import Any, Tuple

import dash
from casino_calendar.logging.config import setup_logger
from casino_calendar.services.colors import get_color
from casino_calendar.settings import APP_TIMEZONE
from dash import ALL, Input, Output, State, dcc, html, no_update
from dash._callback import NoUpdate

from ..services.layout_state import build_event_info_rows, to_naive_utc
from ..visualization import charts as day_charts

PDT = APP_TIMEZONE

# Initialize module logger
logger = setup_logger(__name__)


def register_callbacks(app, df) -> None:
    """Register event related callbacks on the given Dash ``app``."""
    logger.info("Registering event callbacks")

    @app.callback(
        Output("overflow-box", "className"),
        Output("overflow-toggle", "children"),
        Input("overflow-toggle", "n_clicks"),
        State("overflow-date", "data"),
        prevent_initial_call=True,
    )
    def toggle_overflow(n_clicks: int, start_date_str: str) -> Tuple[str, str]:
        """Toggle visibility of the overflow list for the selected week."""
        logger.debug("Overflow toggle received %s click(s) for %s", n_clicks, start_date_str)

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = start_date + timedelta(days=6)
            is_open = n_clicks % 2 == 1

            box_class = "overflow-box-expand show" if is_open else "overflow-box-expand"

            date_range = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
            button_text = (
                f"\U0001f300 Hide Ongoing Events for {date_range}"
                if is_open
                else f"\U0001f300 Show Ongoing Events for {date_range}"
            )

            logger.debug("Overflow toggle state open %s with class %s", is_open, box_class)
            return box_class, button_text

        except Exception as e:
            logger.error("toggle_overflow callback failed: %s", e, exc_info=True)
            raise

    @app.callback(
        Output("event-modal", "style"),
        Output("event-modal", "className"),
        Output("event-modal-body", "children"),
        Output("close-timer", "n_intervals"),
        Output("close-timer", "disabled"),
        Output("day-modal", "style"),
        Output("day-modal", "className"),
        Output("day-modal-body", "children"),
        Input("day-event-catcher", "clickData"),
        Input("close-modal", "n_clicks"),
        Input("close-timer", "n_intervals"),
        Input("close-day-modal", "n_clicks"),
        Input({"type": "grid-event", "index": ALL}, "n_clicks"),
        Input({"type": "day-column", "index": ALL}, "n_clicks"),
        State("week-offset", "data"),
        State("screen-width", "data"),
        State("selected-casinos", "data"),
        State("event-modal", "className"),
        prevent_initial_call=True,
    )
    def show_event_modal(
        day_click: dict | None,
        _close_clicks: int,
        _timer_tick: int,
        _close_day_clicks: int,
        _grid_clicks: list[int],
        _day_column_clicks: list[int],
        week_offset: int,
        screen_width: int,
        selected_casinos: list[str] | None,
        event_modal_class: str | None = None,
    ) -> Tuple[Any, Any, Any, int | NoUpdate, bool | NoUpdate, Any, Any, Any]:
        """Handle modal open and close events.

        Unused parameters prefixed with an underscore are included solely so the
        callback fires when those inputs change.
        """
        start_time = time.time()
        logger.debug("show_event_modal callback triggered")

        try:
            ctx = dash.callback_context
            triggered_id = ctx.triggered_id
            logger.debug("Trigger source: %s", triggered_id)

            def _lookup_click_value(target_id: Any, position: int) -> int | None:
                """Return the n_clicks value for a pattern-matched component."""
                try:
                    inputs = ctx.inputs_list[position]
                except (AttributeError, IndexError):  # pragma: no cover - dash internals
                    inputs = None

                if inputs:
                    for item in inputs:
                        try:
                            if item.get("id") == target_id:
                                return item.get("value")
                        except AttributeError:
                            continue

                try:
                    return ctx.triggered[0]["value"] if ctx.triggered else None
                except (IndexError, KeyError, TypeError, AttributeError):
                    return None

            if triggered_id == "close-timer":
                logger.debug("Closing modal via timer")
                return (
                    {"display": "none"},
                    "modal",
                    "",
                    0,
                    True,
                    no_update,
                    no_update,
                    no_update,
                )

            if triggered_id == "close-modal":
                logger.debug("Closing event modal")
                # Close immediately to ensure click layer is removed
                reopen_day = bool(event_modal_class and "from-day" in event_modal_class)
                return (
                    {"display": "none"},
                    "modal closing",
                    no_update,
                    0,
                    False,
                    {} if reopen_day else no_update,
                    "modal show" if reopen_day else no_update,
                    no_update,
                )

            if triggered_id == "close-day-modal":
                logger.debug("Closing day modal")
                # Hide the day modal but keep its children so the catcher ID exists
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    {"display": "none"},
                    "modal",
                    no_update,
                )

            if isinstance(triggered_id, dict) and triggered_id.get("type") in ("grid-event",):
                logger.debug("Grid event clicked: %s", triggered_id)
                triggered_n = _lookup_click_value(triggered_id, 4)
                if not triggered_n:
                    logger.debug("No triggered value, preventing update")
                    raise dash.exceptions.PreventUpdate

                idx = triggered_id.get("index")

                if idx is None or idx not in df.index:
                    logger.warning("Invalid event index: %s", idx)
                    return (
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                    )

                row = df.loc[idx]
                event_name = row["EventName"] if "EventName" in row.index else "Unknown Event"
                logger.info("Opening event modal for %s", event_name)
                colors = get_color()
                casino_colors = colors.get(row["Casino"], {"bg": "#000", "text": "#000"})
                rows = build_event_info_rows(row.items())
                style = {"--bg": casino_colors["bg"]}
                return (
                    style,
                    "modal show",
                    rows,
                    0,
                    True,
                    {"display": "none"},
                    "modal",
                    no_update,
                )

            if isinstance(triggered_id, dict) and triggered_id.get("type") == "day-column":
                logger.debug("Day column clicked: %s", triggered_id)
                triggered_n = _lookup_click_value(triggered_id, 5)
                if not triggered_n:
                    logger.debug("No triggered value for day column, preventing update")
                    raise dash.exceptions.PreventUpdate

                date_str = triggered_id.get("index")
                if not date_str:
                    logger.warning("No date string provided for day column click")
                    return (
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                    )

                clicked_date = to_naive_utc(datetime.strptime(date_str, "%Y-%m-%d"))
                logger.info("Opening day modal for %s", clicked_date.strftime("%Y-%m-%d"))

                filtered = df[df["Casino"].isin(selected_casinos)] if selected_casinos else df
                logger.debug(
                    "Filtered events to %d items based on selected casinos",
                    len(filtered),
                )

                title_text, grid_children, figure, height_px = day_charts.generate_day_view_parts(
                    filtered, clicked_date, get_color, screen_width
                )
                day_modal_children = html.Div(
                    id="day-modal-content-container",
                    className="base-padding",
                    children=[
                        html.H2(
                            id="day-modal-title",
                            className="day-label day-modal-title",
                            children=title_text,
                        ),
                        html.Div(
                            id="day-grid-wrapper",
                            style={"position": "relative"},
                            children=[
                                html.Div(id="day-grid-content", children=grid_children),
                                dcc.Graph(
                                    id="day-event-catcher",
                                    className="day-event-catcher",
                                    figure=figure,
                                    config={"displayModeBar": False},
                                    style={
                                        "height": f"{height_px}px",
                                        "pointerEvents": "auto",
                                    },
                                ),
                            ],
                        ),
                    ],
                )

                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    {},
                    "modal show",
                    day_modal_children,
                )

            click_data = None
            if triggered_id == "day-event-catcher":
                click_data = day_click

            if click_data and "points" in click_data and click_data["points"]:
                logger.debug("Processing day-event-catcher click data")
                try:
                    data = click_data["points"][0].get("customdata", [None])[0]
                except (IndexError, KeyError, TypeError) as e:
                    logger.warning("Error accessing click data: %s", e)
                    data = None
                if data and data.get("type") == "day_click":
                    day_index = data.get("day_index")
                    if day_index is None:
                        logger.warning("Day index is None in click data")
                        return (
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                        )

                    today = datetime.utcnow()
                    current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
                    week_start = current_sunday + timedelta(weeks=week_offset)
                    clicked_date = week_start + timedelta(days=day_index)

                    logger.info(
                        "Opening day modal for index %s on %s",
                        day_index,
                        clicked_date.strftime("%Y-%m-%d"),
                    )

                    filtered = df[df["Casino"].isin(selected_casinos)] if selected_casinos else df
                    title_text, grid_children, figure, height_px = day_charts.generate_day_view_parts(
                        filtered, clicked_date, get_color, screen_width
                    )
                    day_modal_children = html.Div(
                        id="day-modal-content-container",
                        className="base-padding",
                        children=[
                            html.H2(
                                id="day-modal-title",
                                className="day-label day-modal-title",
                                children=title_text,
                            ),
                            html.Div(
                                id="day-grid-wrapper",
                                style={"position": "relative"},
                                children=[
                                    html.Div(id="day-grid-content", children=grid_children),
                                    dcc.Graph(
                                        id="day-event-catcher",
                                        className="day-event-catcher",
                                        figure=figure,
                                        config={"displayModeBar": False},
                                        style={
                                            "height": f"{height_px}px",
                                            "pointerEvents": "auto",
                                        },
                                    ),
                                ],
                            ),
                        ],
                    )

                    return (
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        {},
                        "modal show",
                        day_modal_children,
                    )

                if data and all(
                    k in data
                    for k in [
                        "EventName",
                        "Casino",
                        "OfferType",
                        "StartDate",
                        "EndDate",
                        "Offer",
                    ]
                ):
                    event_name = data.get("EventName", "Unknown Event")
                    logger.info("Opening event modal for %s", event_name)
                    rows = build_event_info_rows(data.items())
                    return (
                        {},
                        "modal show from-day",
                        rows,
                        0,
                        True,
                        {"display": "none"},
                        "modal",
                        no_update,
                    )

            logger.debug("No valid trigger found, preventing update")
            end_time = time.time()
            logger.debug(
                "show_event_modal callback finished in %.3f seconds (PreventUpdate)",
                end_time - start_time,
            )
            raise dash.exceptions.PreventUpdate

        except dash.exceptions.PreventUpdate:
            # PreventUpdate is expected behavior, not an error - just re-raise it
            end_time = time.time()
            logger.debug(
                "show_event_modal callback finished in %.3f seconds (PreventUpdate)",
                end_time - start_time,
            )
            raise
        except Exception as e:
            logger.error("show_event_modal callback failed: %s", e, exc_info=True)
            # Log performance even on error
            end_time = time.time()
            logger.debug(
                "show_event_modal callback finished in %.3f seconds (error)",
                end_time - start_time,
            )
            raise

    logger.info("Event callbacks ready")
