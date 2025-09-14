from datetime import datetime, timedelta
from typing import Any, Tuple, cast
from uuid import uuid4

import dash
import pandas as pd
from dash import ALL, Input, Output, State, html
from pytz import timezone

from ..logging_config import setup_logger
from ..utils import filter_long_spanning_events, to_naive_utc, to_pdt
from ..week_grid_layout import render_day_labels, render_week_grid

PDT = timezone("America/Los_Angeles")

# Initialize module logger
logger = setup_logger(__name__)


def _get_hotel_booking_sites():
    """Get hotel booking sites data from configuration cache."""
    from utils.config_cache import get_config

    sites = get_config("hotel_book_sites.json")
    if not sites:
        logger.warning(
            "hotel_book_sites.json not available, hotel booking links disabled"
        )
        return {}
    return sites


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
        logger.debug(f"Casino legend clicked: {clicked}")

        if not selected:
            selected = []

        selected_list = list(selected)
        if clicked in selected_list:
            selected_list.remove(clicked)
        else:
            selected_list.append(clicked)

        logger.info(f"Selected casinos updated: {selected_list}")
        return selected_list

    @app.callback(
        Output({"type": "casino-filter", "index": ALL}, "className"),
        Input("selected-casinos", "data"),
        State({"type": "casino-filter", "index": ALL}, "id"),
    )
    def update_legend_classes(selected, ids):
        logger.debug(f"Updating legend classes for casinos: {selected}")
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
        Output("selected-event-types", "data"),
        Input("event-type-filter", "value"),
        prevent_initial_call=True,
    )
    def update_event_type_filter(selected_types: list[str] | None) -> list[str]:
        logger.debug(f"Event type filter changed: {selected_types}")
        logger.info(f"Selected event types updated: {selected_types}")
        return selected_types or []

    @app.callback(
        Output("hotel-booking-container", "children"),
        Output("hotel-booking-container", "style"),
        Input("selected-casinos", "data"),
    )
    def update_hotel_booking_link(selected_casinos):
        """Update hotel booking link based on selected casino."""
        logger.debug(f"Updating hotel booking link for selection: {selected_casinos}")
        if not selected_casinos or len(selected_casinos) != 1:
            logger.debug("Hotel booking link hidden due to selection count")
            return [], {"display": "none", "textAlign": "center", "marginTop": "10px"}

        casino_name = selected_casinos[0]
        hotel_booking_sites = _get_hotel_booking_sites()
        booking_url = hotel_booking_sites.get(casino_name)

        if booking_url and booking_url != "N/A":
            logger.info(f"Showing hotel booking link for {casino_name}")
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
        logger.info(f"No booking URL for {casino_name}; hiding hotel booking link")
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
        Input("selected-event-types", "data"),
        prevent_initial_call=True,
    )
    def render_single_week_chart(
        usable_height: int,
        week_offset: int,
        screen_width: int,
        selected_casinos: list[str] | None,
        selected_types: list[str] | None,
    ) -> Tuple[html.Div, list[html.Div], str, str, dict[str, Any]]:
        """Render a single week of events and overflow list."""
        ctx = dash.callback_context
        logger.debug(
            "Rendering week chart: offset=%s casinos=%s types=%s triggered_by=%s",
            week_offset,
            selected_casinos,
            selected_types,
            ctx.triggered_id,
        )
        today_pdt = datetime.now(PDT)
        current_sunday = today_pdt - timedelta(days=(today_pdt.weekday() + 1) % 7)
        week_start_pdt = current_sunday + timedelta(weeks=week_offset)
        week_start = to_naive_utc(week_start_pdt)

        filtered_df = df
        if selected_casinos:
            logger.debug(f"Filtering events by casinos: {selected_casinos}")
            filtered_df = filtered_df[filtered_df["Casino"].isin(selected_casinos)]
        if selected_types:
            logger.debug(f"Filtering events by types: {selected_types}")
            filtered_df = filtered_df[filtered_df["OfferType"].isin(selected_types)]
        logger.info(f"Filtered events count: {len(filtered_df)}")

        grid = render_week_grid(week_start, filtered_df, screen_width, selected_casinos)
        labels = render_day_labels(week_start)

        week_end = week_start + timedelta(days=7)
        overflow_df = filter_long_spanning_events(filtered_df, week_start, week_end)

        if not overflow_df.empty:
            week_start_pdt = to_pdt(week_start)
            week_end_pdt = to_pdt(week_end)
            is_open = bool(selected_casinos or selected_types)
            week_range = (
                f"{week_start_pdt.strftime('%b %d')} - {week_end_pdt.strftime('%b %d')}"
            )
            toggle_text = (
                f"\U0001f300 Hide Ongoing Events for {week_range}"
                if is_open
                else f"\U0001f300 Show Ongoing Events for {week_range}"
            )
            overflow_toggle = html.Button(
                toggle_text,
                id="overflow-toggle",
                n_clicks=1 if is_open else 0,
                className="overflow-toggle",
            )

            def _format_overflow_item(row: pd.Series) -> html.Li:
                start = to_pdt(cast(datetime, row["StartDate"])).strftime("%b %d")
                end = to_pdt(cast(datetime, row["EndDate"])).strftime("%b %d")
                text = f"{row['EventName']} ({row['Casino']}) - {start} to {end}"
                return html.Li(text)

            overflow_box = html.Div(
                id="overflow-box",
                className="overflow-box-expand" + (" show" if is_open else ""),
                children=[
                    html.Strong(
                        "Ongoing Events This Week:",
                        className="overflow-title font-bold mb-section",
                        style={"display": "block"},
                    ),
                    html.Ul(
                        [
                            _format_overflow_item(row)
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
            className="week-chart-scroll",
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
            requestAnimationFrame(() => {
                const container = document.getElementById('week-chart-container');
                if (!container) { return; }

                const weekLabel = document.getElementById('week-label');
                if (weekLabel) {
                    weekLabel.classList.remove('slide-in', 'slide-init');
                    void weekLabel.offsetWidth;
                    weekLabel.classList.add('slide-init', 'slide-in');
                }

                const dayRow = document.getElementById('day-label-row');
                if (dayRow) {
                    dayRow.classList.remove('slide-in', 'slide-init');
                    void dayRow.offsetWidth;
                    dayRow.classList.add('slide-init', 'slide-in');
                }

                const chart = container.querySelector('.week-chart-scroll');
                if (chart) {
                    chart.classList.remove('slide-in', 'slide-init');
                    void chart.offsetWidth;
                    chart.classList.add('slide-init', 'slide-in');
                }
            });
            return '';
        }
        """,
        Output("animation-dummy", "children"),
        Input("animation-refresh", "data"),
    )
