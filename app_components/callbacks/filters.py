import json
import time
from datetime import datetime, timedelta
from typing import Any, Tuple, cast
from uuid import uuid4

import dash
from dash import ALL, Input, Output, State, html
from pytz import timezone

from ..logging_config import setup_logger
from ..utils import filter_long_spanning_events, to_naive_utc, to_pdt
from ..week_grid_layout import render_day_labels, render_week_grid

PDT = timezone("America/Los_Angeles")

# Initialize module logger
logger = setup_logger(__name__)

# Load hotel booking sites data
try:
    with open("data/hotel_book_sites.json", "r") as f:
        HOTEL_BOOKING_SITES = json.load(f)
except FileNotFoundError:
    logger.warning("hotel_book_sites.json not found, hotel booking links disabled")
    HOTEL_BOOKING_SITES = {}
except json.JSONDecodeError as e:
    logger.error(f"Error parsing hotel_book_sites.json: {e}")
    HOTEL_BOOKING_SITES = {}


def register_callbacks(app, df) -> None:
    """Register filter and navigation callbacks."""
    logger.info("Registering filter and navigation callbacks")

    app.clientside_callback(
        """
        function(n_intervals) {
            const width = window.innerWidth;
            const height = window.innerHeight;
            const header = document.getElementById('app-header');
            const headerHeight = header ? header.offsetHeight : 100;
            const usable = Math.max(height - headerHeight - 20, 300);

            return [width, usable];
        }
        """,
        Output("screen-width", "data"),
        Output("usable-height", "data"),
        Input("initial-trigger", "n_intervals"),
    )
    logger.debug("Registered clientside callback for screen dimensions")

    @app.callback(Output("week-label", "children"), Input("week-offset", "data"))
    def update_week_label(week_offset: int) -> str:
        """Return a label for the currently selected week."""
        logger.debug(f"Updating week label for offset: {week_offset}")

        try:
            today_pdt = datetime.now(PDT)
            current_sunday = today_pdt - timedelta(days=(today_pdt.weekday() + 1) % 7)
            week_start_pdt = current_sunday + timedelta(weeks=week_offset)
            week_end_pdt = week_start_pdt + timedelta(days=6)

            label = (
                f"Events for the Week of {week_start_pdt.strftime('%B %d')} - "
                f"{week_end_pdt.strftime('%B %d, %Y')}"
            )
            logger.debug(f"Generated week label: {label}")
            return label

        except Exception as e:
            logger.error(f"Error generating week label: {e}", exc_info=True)
            return "Events for Current Week"

    @app.callback(
        Output("week-offset", "data"),
        Output("prev-button", "disabled"),
        Output("next-button", "disabled"),
        Output("next-button", "title"),
        Input("prev-button", "n_clicks"),
        Input("next-button", "n_clicks"),
        State("week-offset", "data"),
    )
    def update_week_offset(
        _prev_clicks: int,
        _next_clicks: int,
        current_offset: int,
    ) -> Tuple[int, bool, bool, str]:
        """Update the week offset based on navigation button clicks."""
        ctx = dash.callback_context
        desired_offset = current_offset

        if ctx.triggered_id == "prev-button":
            desired_offset -= 1
        elif ctx.triggered_id == "next-button":
            desired_offset += 1

        desired_offset = max(-6, desired_offset)
        today_pdt = datetime.now(PDT)
        current_sunday = today_pdt - timedelta(days=(today_pdt.weekday() + 1) % 7)

        next_week_offset = desired_offset + 1
        next_week_start_pdt = current_sunday + timedelta(weeks=next_week_offset)
        next_week_start = to_naive_utc(next_week_start_pdt)
        next_week_end = next_week_start + timedelta(days=7)

        has_next_week_events = not df[
            (df["EndDate"] > next_week_start) & (df["StartDate"] < next_week_end)
        ].empty

        if not has_next_week_events and desired_offset > current_offset:
            desired_offset = current_offset

        prev_disabled = desired_offset <= -6
        next_disabled = not has_next_week_events
        next_title = "No Upcoming events" if next_disabled else "Upcoming Week"
        return desired_offset, prev_disabled, next_disabled, next_title

    @app.callback(
        Output("selected-casinos", "data"),
        Input({"type": "casino-filter", "index": ALL}, "n_clicks"),
        State({"type": "casino-filter", "index": ALL}, "id"),
        State("selected-casinos", "data"),
        prevent_initial_call=True,
    )
    def toggle_casino_filter(n_clicks, ids, selected):
        ctx = dash.callback_context
        if not ctx.triggered_id:
            raise dash.exceptions.PreventUpdate
        clicked = ctx.triggered_id.get("index")

        if not selected:
            selected = []

        if clicked in selected:
            selected = []
        else:
            selected = [clicked]

        return selected

    @app.callback(
        Output({"type": "casino-filter", "index": ALL}, "className"),
        Input("selected-casinos", "data"),
        State({"type": "casino-filter", "index": ALL}, "id"),
    )
    def update_legend_classes(selected, ids):
        base = "legend-item legend-button"
        selected_set = set(selected or [])
        classes = []
        for item in ids:
            cls = base
            if item.get("index") in selected_set:
                cls += " legend-selected"
            classes.append(cls)
        return classes

    @app.callback(
        Output("hotel-booking-container", "children"),
        Output("hotel-booking-container", "style"),
        Input("selected-casinos", "data"),
    )
    def update_hotel_booking_link(selected_casinos):
        """Update hotel booking link based on selected casino."""
        if not selected_casinos or len(selected_casinos) != 1:
            # Hide the container if no casino or multiple casinos are selected
            return [], {"display": "none", "textAlign": "center", "marginTop": "10px"}

        casino_name = selected_casinos[0]
        booking_url = HOTEL_BOOKING_SITES.get(casino_name)

        if booking_url and booking_url != "N/A":
            # Show the hotel booking link
            link_content = html.A(
                "🏨 Hotel Booking",
                href=booking_url,
                target="_blank",
            )
            return [link_content], {
                "display": "block",
                "textAlign": "center",
                "marginTop": "10px",
            }
        else:
            # Hide the container if no booking URL or N/A
            return [], {"display": "none", "textAlign": "center", "marginTop": "10px"}

    @app.callback(
        Output("week-chart-container", "children"),
        Output("day-label-row", "children"),
        Output("overflow-date", "data"),
        Output("animation-refresh", "data"),
        Output("calendar-scroll-body", "style"),
        Input("usable-height", "data"),
        Input("week-offset", "data"),
        Input("screen-width", "data"),
        Input("selected-casinos", "data"),
        prevent_initial_call=True,
    )
    def render_single_week_chart(
        usable_height: int,
        week_offset: int,
        screen_width: int,
        selected_casinos: list[str] | None,
    ) -> Tuple[html.Div, list[html.Div], str, str, dict[str, Any]]:
        """Render a single week of events and overflow list."""
        today_pdt = datetime.now(PDT)
        current_sunday = today_pdt - timedelta(days=(today_pdt.weekday() + 1) % 7)
        week_start_pdt = current_sunday + timedelta(weeks=week_offset)
        week_start = to_naive_utc(week_start_pdt)

        filtered_df = (
            df[df["Casino"].isin(selected_casinos)] if selected_casinos else df
        )
        grid = render_week_grid(week_start, filtered_df, screen_width, selected_casinos)
        labels = render_day_labels(week_start)

        week_end = week_start + timedelta(days=7)
        overflow_df = filter_long_spanning_events(filtered_df, week_start, week_end)

        if not overflow_df.empty:
            week_start_pdt = to_pdt(week_start)
            week_end_pdt = to_pdt(week_end)
            is_open = bool(selected_casinos)
            toggle_text = (
                f"\U0001f300 Hide Ongoing Events for {week_start_pdt.strftime('%b %d')} - {week_end_pdt.strftime('%b %d')}"
                if is_open
                else f"\U0001f300 Show Ongoing Events for {week_start_pdt.strftime('%b %d')} - {week_end_pdt.strftime('%b %d')}"
            )
            overflow_toggle = html.Button(
                toggle_text,
                id="overflow-toggle",
                n_clicks=1 if is_open else 0,
                className="overflow-toggle",
            )
            overflow_box = html.Div(
                id="overflow-box",
                className="overflow-box-expand" + (" show" if is_open else ""),
                children=[
                    html.Strong(
                        "Ongoing Events This Week:",
                        className="font-bold mb-section",
                        style={"color": "#6A5ACD", "display": "block"},
                    ),
                    html.Ul(
                        [
                            html.Li(
                                f"{row['EventName']} ({row['Casino']}) - "
                                f"{to_pdt(cast(datetime, row['StartDate'])).strftime('%b %d')} to "
                                f"{to_pdt(cast(datetime, row['EndDate'])).strftime('%b %d')}",
                                style={"color": "#00008B"},
                            )
                            for _, row in overflow_df.iterrows()
                        ]
                    ),
                ],
            )
        else:
            overflow_toggle = html.Div()
            overflow_box = html.Div()

        data_attr: dict[str, Any] = {"data-week": str(week_offset)}
        chart = html.Div(
            children=[grid, overflow_toggle, overflow_box],
            id=f"week-chart-{week_offset}",
            className="slide-init slide-in week-chart-scroll",
            **data_attr,
        )

        style = (
            {"height": f"{usable_height}px"}
            if screen_width >= 768
            else {"minHeight": f"{usable_height}px"}
        )

        return chart, labels, week_start.strftime("%Y-%m-%d"), str(uuid4()), style

    app.clientside_callback(
        """
        function(refresh) {
            setTimeout(function() {
                const container = document.getElementById('week-chart-container');
                if (!container) { return; }
                const weekLabel = document.getElementById('week-label');
                if (weekLabel) {
                    weekLabel.classList.remove('slide-in');
                    void weekLabel.offsetWidth;
                    weekLabel.classList.add('slide-in');
                }
                const dayRow = document.getElementById('day-label-row');
                if (dayRow) {
                    dayRow.classList.remove('slide-in');
                    void dayRow.offsetWidth;
                    dayRow.classList.add('slide-in');
                }
                const chart = container.querySelector('.week-chart-scroll');
                if (!chart) { return; }
                chart.classList.remove('slide-in');
                void chart.offsetWidth;
                chart.classList.add('slide-in');
            }, 0);
            return '';
        }
        """,
        Output("animation-dummy", "children"),
        Input("animation-refresh", "data"),
    )
