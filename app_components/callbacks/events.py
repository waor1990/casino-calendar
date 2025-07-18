from datetime import datetime, timedelta
from typing import Any, Tuple

import dash
from dash import ALL, Input, Output, State, no_update
from dash._callback import NoUpdate
from pytz import timezone

from utils.colors import get_color
from utils.data_parsing import prepare_week_events  # noqa: F401

from ..plotting import generate_day_view_html
from ..utils import build_event_info_rows, to_naive_utc

PDT = timezone("America/Los_Angeles")


def register_callbacks(app, df) -> None:
    """Register event related callbacks on the given Dash ``app``."""

    @app.callback(
        Output("overflow-box", "className"),
        Output("overflow-toggle", "children"),
        Input("overflow-toggle", "n_clicks"),
        State("overflow-date", "data"),
        prevent_initial_call=True,
    )
    def toggle_overflow(n_clicks: int, start_date_str: str) -> Tuple[str, str]:
        """Toggle visibility of the overflow list for the selected week."""
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = start_date + timedelta(days=6)
        is_open = n_clicks % 2 == 1

        box_class = "overflow-box-expand show" if is_open else "overflow-box-expand"

        button_text = (
            f"\U0001f300 Hide Ongoing Events for {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
            if is_open
            else f"\U0001f300 Show Ongoing Events for {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
        )

        return box_class, button_text

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
        ctx = dash.callback_context
        triggered_id = ctx.triggered_id

        if triggered_id == "close-timer":
            return no_update, "", "", 0, {"display": "none"}, "", ""

        if triggered_id == "close-modal":
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
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                {"display": "none"},
                "modal closing",
                "",
            )

        if isinstance(triggered_id, dict) and triggered_id.get("type") == "grid-event":
            triggered_n = ctx.triggered[0]["value"] if ctx.triggered else None
            if not triggered_n:
                raise dash.exceptions.PreventUpdate

            idx = triggered_id.get("index")

            if idx is None or idx not in df.index:
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
            rows = build_event_info_rows(row.items())
            return ({}, "modal show", rows, 0, {"display": "none"}, "", "")

        if isinstance(triggered_id, dict) and triggered_id.get("type") == "day-column":
            triggered_n = ctx.triggered[0]["value"] if ctx.triggered else None
            if not triggered_n:
                raise dash.exceptions.PreventUpdate

            date_str = triggered_id.get("index")
            if not date_str:
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
            filtered = (
                df[df["Casino"].isin(selected_casinos)] if selected_casinos else df
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
            data = click_data["points"][0].get("customdata", [None])[0]
            if data and data.get("type") == "day_click":
                day_index = data.get("day_index")
                if day_index is None:
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
                filtered = (
                    df[df["Casino"].isin(selected_casinos)] if selected_casinos else df
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
                rows = build_event_info_rows(data.items())
                return ({}, "modal show", rows, 0, {"display": "none"}, "", "")

        raise dash.exceptions.PreventUpdate
