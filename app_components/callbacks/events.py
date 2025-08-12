import time
from datetime import datetime, timedelta
from typing import Any, Tuple

import dash
from dash import ALL, Input, Output, State, no_update
from dash._callback import NoUpdate
from pytz import timezone

from utils.colors import get_color
from utils.data_parsing import prepare_week_events  # noqa: F401

from ..logging_config import setup_logger
from ..plotting import generate_day_view_html
from ..utils import build_event_info_rows, to_naive_utc

PDT = timezone("America/Los_Angeles")

# Initialize module logger
logger = setup_logger(__name__)


def register_callbacks(app, df) -> None:
    """Register event related callbacks on the given Dash ``app``."""
    logger.info("Registering event-related callbacks")

    @app.callback(
        Output("overflow-box", "className"),
        Output("overflow-toggle", "children"),
        Input("overflow-toggle", "n_clicks"),
        State("overflow-date", "data"),
        prevent_initial_call=True,
    )
    def toggle_overflow(n_clicks: int, start_date_str: str) -> Tuple[str, str]:
        """Toggle visibility of the overflow list for the selected week."""
        logger.debug(
            f"Toggle overflow called with n_clicks={n_clicks}, date={start_date_str}"
        )

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = start_date + timedelta(days=6)
            is_open = n_clicks % 2 == 1

            box_class = "overflow-box-expand show" if is_open else "overflow-box-expand"

            date_range = (
                f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
            )
            button_text = (
                f"\U0001f300 Hide Ongoing Events for {date_range}"
                if is_open
                else f"\U0001f300 Show Ongoing Events for {date_range}"
            )

            logger.debug(f"Overflow toggled: is_open={is_open}, class={box_class}")
            return box_class, button_text

        except Exception as e:
            logger.error(f"Error in toggle_overflow callback: {e}", exc_info=True)
            raise

    @app.callback(
        Output("event-modal", "style"),
        Output("event-modal", "className"),
        Output("event-modal-body", "children"),
        Output("close-timer", "n_intervals"),
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
    ) -> Tuple[Any, Any, Any, int | NoUpdate, Any, Any, Any]:
        """Handle modal open and close events.

        Unused parameters prefixed with an underscore are included solely so the
        callback fires when those inputs change.
        """
        start_time = time.time()
        logger.debug("show_event_modal callback triggered")

        try:
            ctx = dash.callback_context
            triggered_id = ctx.triggered_id
            logger.debug(f"Triggered by: {triggered_id}")

            if triggered_id == "close-timer":
                logger.debug("Closing modal via timer")
                return no_update, "", "", 0, {"display": "none"}, "", ""

            if triggered_id == "close-modal":
                logger.debug("Closing event modal")
                return (
                    no_update,
                    "modal closing",
                    no_update,
                    1,
                    {"display": "none"},
                    no_update,
                    no_update,
                )

            if triggered_id == "close-day-modal":
                logger.debug("Closing day modal")
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    {"display": "none"},
                    "modal closing",
                    "",
                )

            if (
                isinstance(triggered_id, dict)
                and triggered_id.get("type") == "grid-event"
            ):
                logger.debug(f"Grid event clicked: {triggered_id}")
                try:
                    triggered_n = (
                        ctx.triggered[0]["value"]
                        if ctx.triggered and len(ctx.triggered) > 0
                        else None
                    )
                except (IndexError, KeyError, TypeError):
                    triggered_n = None
                if not triggered_n:
                    logger.debug("No triggered value, preventing update")
                    raise dash.exceptions.PreventUpdate

                idx = triggered_id.get("index")

                if idx is None or idx not in df.index:
                    logger.warning(f"Invalid event index: {idx}")
                    return (
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                    )

                row = df.loc[idx]
                event_name = (
                    row["EventName"] if "EventName" in row.index else "Unknown Event"
                )
                logger.info(f"Opening event modal for: {event_name}")
                colors = get_color()
                casino_colors = colors.get(
                    row["Casino"], {"bg": "#000", "text": "#000"}
                )
                rows = build_event_info_rows(row.items())
                style = {"--bg": casino_colors["bg"]}
                return (style, "modal show", rows, 0, {"display": "none"}, "", "")

            if (
                isinstance(triggered_id, dict)
                and triggered_id.get("type") == "day-column"
            ):
                logger.debug(f"Day column clicked: {triggered_id}")
                try:
                    triggered_n = (
                        ctx.triggered[0]["value"]
                        if ctx.triggered and len(ctx.triggered) > 0
                        else None
                    )
                except (IndexError, KeyError, TypeError):
                    triggered_n = None
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
                    )

                clicked_date = to_naive_utc(datetime.strptime(date_str, "%Y-%m-%d"))
                logger.info(
                    f"Opening day modal for: {clicked_date.strftime('%Y-%m-%d')}"
                )

                filtered = (
                    df[df["Casino"].isin(selected_casinos)] if selected_casinos else df
                )
                logger.debug(
                    "Filtered events to %d items based on selected casinos",
                    len(filtered),
                )

                content = generate_day_view_html(
                    filtered, clicked_date, get_color, screen_width
                )

                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    {},
                    "modal show",
                    content,
                )

            click_data = None
            if triggered_id == "day-event-catcher":
                click_data = day_click

            if click_data and "points" in click_data and click_data["points"]:
                logger.debug("Processing day-event-catcher click data")
                try:
                    data = click_data["points"][0].get("customdata", [None])[0]
                except (IndexError, KeyError, TypeError) as e:
                    logger.warning(f"Error accessing click data: {e}")
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
                        )

                    today = datetime.utcnow()
                    current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
                    week_start = current_sunday + timedelta(weeks=week_offset)
                    clicked_date = week_start + timedelta(days=day_index)

                    logger.info(
                        f"Opening day modal for day index {day_index}: "
                        f"{clicked_date.strftime('%Y-%m-%d')}"
                    )

                    filtered = (
                        df[df["Casino"].isin(selected_casinos)]
                        if selected_casinos
                        else df
                    )
                    content = generate_day_view_html(
                        filtered, clicked_date, get_color, screen_width
                    )

                    return (
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        {},
                        "modal show",
                        content,
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
                    logger.info(
                        f"Opening event modal for: "
                        f"{data.get('EventName', 'Unknown Event')}"
                    )
                    rows = build_event_info_rows(data.items())
                    return ({}, "modal show", rows, 0, {"display": "none"}, "", "")

            logger.debug("No valid trigger found, preventing update")
            end_time = time.time()
            logger.debug(
                f"show_event_modal callback completed in "
                f"{end_time - start_time:.3f}s (PreventUpdate)"
            )
            raise dash.exceptions.PreventUpdate

        except dash.exceptions.PreventUpdate:
            # PreventUpdate is expected behavior, not an error - just re-raise it
            end_time = time.time()
            logger.debug(
                f"show_event_modal callback completed in "
                f"{end_time - start_time:.3f}s (PreventUpdate)"
            )
            raise
        except Exception as e:
            logger.error(f"Error in show_event_modal callback: {e}", exc_info=True)
            # Log performance even on error
            end_time = time.time()
            logger.debug(
                f"show_event_modal callback completed in "
                f"{end_time - start_time:.3f}s (with error)"
            )
            raise

    logger.info("Event callbacks registered successfully")
