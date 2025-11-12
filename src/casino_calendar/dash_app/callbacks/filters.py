"""Callbacks for casino filtering, hotel booking links, and derived views."""

from datetime import datetime, timedelta
from typing import Any, Tuple, cast
from uuid import uuid4

import dash
import pandas as pd
from dash import ALL, Input, Output, State, html, no_update

from casino_calendar.logging.config import setup_logger
from casino_calendar.settings import APP_TIMEZONE

from ..layout import week_grid
from ..services import layout_state

PDT = APP_TIMEZONE

# Initialize module logger
logger = setup_logger(__name__)


def _get_hotel_booking_sites():
    """Get hotel booking sites data from configuration cache."""
    from casino_calendar.services.config_cache import get_config

    sites = get_config("lookups/hotel_book_sites.json")
    if not sites:
        logger.warning(
            "hotel_book_sites.json not available, hotel booking links disabled"
        )
        return {}
    return sites


def register_callbacks(app, df, _repository=None) -> None:
    """Register filter and navigation callbacks."""
    logger.info("Registering filter and navigation callbacks")

    def _week_start_from_offset(week_offset: int) -> datetime:
        """Return the UTC week start for the provided offset."""

        today_pdt = datetime.now(PDT)
        current_sunday = today_pdt - timedelta(days=(today_pdt.weekday() + 1) % 7)
        week_start_pdt = current_sunday + timedelta(weeks=week_offset)
        return layout_state.to_naive_utc(week_start_pdt)

    def _apply_filters(
        source_df: pd.DataFrame,
        casinos: list[str] | None,
        offer_types: list[str] | None,
    ) -> pd.DataFrame:
        """Filter ``source_df`` by casinos and offer types."""

        filtered = source_df
        if casinos:
            filtered = filtered[filtered["Casino"].isin(casinos)]
        if offer_types:
            filtered = filtered[filtered["OfferType"].isin(offer_types)]
        return filtered

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
    logger.debug("Clientside screen dimension callback registered")

    @app.callback(Output("week-label", "children"), Input("week-offset", "data"))
    def update_week_label(week_offset: int) -> str:
        """Return a label for the currently selected week."""
        logger.debug("Updating week label for offset %s", week_offset)

        try:
            today_pdt = datetime.now(PDT)
            current_sunday = today_pdt - timedelta(days=(today_pdt.weekday() + 1) % 7)
            week_start_pdt = current_sunday + timedelta(weeks=week_offset)
            week_end_pdt = week_start_pdt + timedelta(days=6)

            label = (
                f"Events for the Week of {week_start_pdt.strftime('%B %d')} - "
                f"{week_end_pdt.strftime('%B %d, %Y')}"
            )
            logger.debug("Week label generated: %s", label)
            return label

        except Exception as e:
            logger.error("Failed to generate week label: %s", e, exc_info=True)
            return "Events for Current Week"

    @app.callback(
        Output("week-offset", "data"),
        Output("prev-button", "disabled"),
        Output("next-button", "disabled"),
        Output("next-button", "title"),
        Input("prev-button", "n_clicks"),
        Input("next-button", "n_clicks"),
        Input("event-data-refresh", "data"),
        State("week-offset", "data"),
    )
    def update_week_offset(
        _prev_clicks: int,
        _next_clicks: int,
        _refresh_token,
        current_offset: int = 0,
    ) -> Tuple[int, bool, bool, str]:
        """Update the week offset based on navigation button clicks."""
        ctx = dash.callback_context
        desired_offset = current_offset

        trigger_id = ctx.triggered_id

        if trigger_id == "prev-button":
            desired_offset -= 1
        elif trigger_id == "next-button":
            desired_offset += 1
        elif trigger_id == "event-data-refresh":
            desired_offset = current_offset

        desired_offset = max(-6, desired_offset)
        today_pdt = datetime.now(PDT)
        current_sunday = today_pdt - timedelta(days=(today_pdt.weekday() + 1) % 7)

        next_week_offset = desired_offset + 1
        next_week_start_pdt = current_sunday + timedelta(weeks=next_week_offset)
        next_week_start = layout_state.to_naive_utc(next_week_start_pdt)
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
        logger.debug("Casino legend clicked: %s", clicked)

        selected_list = list(selected or [])

        if clicked in selected_list:
            selected_list.remove(clicked)
        else:
            selected_list.append(clicked)

        available_indices = [
            item.get("index")
            for item in ids
            if isinstance(item, dict) and item.get("index")
        ]
        unique_available = {idx for idx in available_indices}
        selected_list = [idx for idx in selected_list if idx in unique_available]

        logger.info("Selected casinos updated: %s", selected_list)
        return selected_list

    @app.callback(
        Output({"type": "casino-filter", "index": ALL}, "className"),
        Input("selected-casinos", "data"),
        State({"type": "casino-filter", "index": ALL}, "id"),
    )
    def update_legend_classes(selected, ids):
        logger.debug("Updating legend classes for casinos: %s", selected)
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
        logger.debug("Event type filter changed: %s", selected_types)
        logger.info("Selected event types updated: %s", selected_types)
        return selected_types or []

    @app.callback(
        Output("event-type-filter", "options"),
        Input("week-offset", "data"),
        Input("selected-casinos", "data"),
        Input("event-data-refresh", "data"),
    )
    def update_event_type_options(
        week_offset: int | None,
        selected_casinos: list[str] | None,
        _refresh_token,
    ) -> list[dict[str, str]] | Any:
        """Return dropdown options annotated with event counts."""

        try:
            try:
                normalized_offset = int(week_offset or 0)
            except (TypeError, ValueError):
                logger.debug(
                    "Invalid week offset provided for event type options: %s",
                    week_offset,
                )
                normalized_offset = 0

            week_start = _week_start_from_offset(normalized_offset)
            week_end = week_start + timedelta(days=7)

            weekly_events = df[
                (df["EndDate"] > week_start) & (df["StartDate"] < week_end)
            ]
            filtered_df = _apply_filters(weekly_events, selected_casinos, None)

            counts = (
                filtered_df["OfferType"].dropna().astype(str).value_counts()
                if not filtered_df.empty
                else pd.Series(dtype=int)
            )

            all_offer_types = sorted(map(str, df["OfferType"].dropna().unique()))

            options = [
                {
                    "label": f"{offer_type} ({int(counts.get(offer_type, 0))})",
                    "value": offer_type,
                }
                for offer_type in all_offer_types
            ]

            logger.debug(
                "Event type options refreshed for casinos=%s week_offset=%s",
                selected_casinos,
                normalized_offset,
            )
            return options

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Failed to refresh event type options: %s", exc, exc_info=True)
            return no_update

    @app.callback(
        Output("hotel-booking-container", "children"),
        Output("hotel-booking-container", "style"),
        Input("selected-casinos", "data"),
    )
    def update_hotel_booking_link(selected_casinos):
        """Update hotel booking link based on selected casino."""
        logger.debug("Updating hotel booking link for selection: %s", selected_casinos)
        if not selected_casinos or len(selected_casinos) != 1:
            logger.debug("Hotel booking link hidden due to selection count")
            return [], {"display": "none", "textAlign": "center", "marginTop": "10px"}

        casino_name = selected_casinos[0]
        hotel_booking_sites = _get_hotel_booking_sites()
        booking_url = hotel_booking_sites.get(casino_name)

        if booking_url and booking_url != "N/A":
            logger.info("Showing hotel booking link for %s", casino_name)
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
        logger.info("Hiding hotel booking link for %s; URL not available", casino_name)
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
        Input("event-data-refresh", "data"),
        prevent_initial_call=True,
    )
    def render_single_week_chart(
        usable_height: int,
        week_offset: int,
        screen_width: int,
        selected_casinos: list[str] | None,
        selected_types: list[str] | None,
        _refresh_token,
    ) -> Tuple[html.Div, list[html.Div], str, str, dict[str, Any]]:
        """Render a single week of events and overflow list."""
        ctx = dash.callback_context
        logger.debug(
            "Rendering week chart with offset %s, casinos %s, types %s, trigger %s",
            week_offset,
            selected_casinos,
            selected_types,
            ctx.triggered_id,
        )
        selected_casinos = selected_casinos or []
        selected_types = selected_types or []
        if selected_casinos:
            logger.debug("Filtering events by casinos: %s", selected_casinos)
        if selected_types:
            logger.debug("Filtering events by types: %s", selected_types)

        week_start = _week_start_from_offset(week_offset)
        filtered_df = _apply_filters(df, selected_casinos, selected_types)
        logger.info("Filtered events count: %d", len(filtered_df))

        grid = week_grid.render_week_grid(
            week_start, filtered_df, screen_width, selected_casinos
        )
        labels = week_grid.render_day_labels(week_start)

        week_end = week_start + timedelta(days=7)
        overflow_df = layout_state.filter_long_spanning_events(
            filtered_df, week_start, week_end
        )

        overflow_toggle: html.Div | html.Button
        overflow_box: html.Div

        if not overflow_df.empty:
            week_start_pdt = layout_state.to_pdt(week_start)
            week_end_pdt = layout_state.to_pdt(week_end)
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
                start = layout_state.to_pdt(cast(datetime, row["StartDate"])).strftime(
                    "%b %d"
                )
                end = layout_state.to_pdt(cast(datetime, row["EndDate"])).strftime(
                    "%b %d"
                )
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
            overflow_toggle = html.Div()  # type: ignore[assignment]
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

    @app.callback(
        Output("calendar-grid", "children"),
        Input("week-offset", "data"),
        Input("screen-width", "data"),
        Input("event-data-refresh", "data"),
        State("event-filter-state", "data"),
        State("legacy-event-data", "data"),
        State("selected-casinos", "data"),
        State("selected-event-types", "data"),
        prevent_initial_call=True,
    )
    def _render_legacy_calendar_grid(
        week_offset: int,
        screen_width: int,
        filter_flags: dict[str, Any] | list[str] | None,
        legacy_data,
        selected_casinos_state,
        selected_types_state,
        _refresh_token=None,
    ):
        """Maintain backwards-compatible calendar grid output for legacy tests."""

        logger.debug(
            "Rendering legacy calendar grid offset=%s screen=%s filter_flags=%s",
            week_offset,
            screen_width,
            filter_flags,
        )

        triggered = getattr(dash.callback_context, "triggered_id", None)
        selected_casinos = (
            selected_casinos_state if isinstance(selected_casinos_state, list) else []
        )
        selected_types = (
            selected_types_state if isinstance(selected_types_state, list) else []
        )

        if isinstance(legacy_data, pd.DataFrame):
            source_df = legacy_data
        elif isinstance(legacy_data, list):
            try:
                source_df = pd.DataFrame(legacy_data)
            except (ValueError, TypeError):
                logger.debug(
                    "Unable to coerce legacy event data into DataFrame; using repository data"
                )
                source_df = df
        else:
            source_df = df

        active_types: list[str] = []
        if isinstance(triggered, dict) and triggered.get("type") == "event-filter":
            toggled = triggered.get("index")
            if isinstance(toggled, str):
                active_types = [toggled]
        elif isinstance(filter_flags, dict):
            active_types = [name for name, enabled in filter_flags.items() if enabled]
        elif isinstance(filter_flags, list):
            active_types = [name for name in filter_flags if isinstance(name, str)]

        if not active_types:
            active_types = selected_types

        week_start = _week_start_from_offset(week_offset)
        filtered_df = _apply_filters(source_df, selected_casinos, active_types)
        logger.debug(
            "Legacy calendar grid filtered to %d events (casinos=%s, types=%s)",
            len(filtered_df),
            selected_casinos,
            active_types,
        )
        return week_grid.render_week_grid(
            week_start, filtered_df, screen_width, selected_casinos
        )

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
