from datetime import datetime, timedelta
from typing import Any, List

import dash
import pandas as pd
from dash import ALL, Input, Output, State, html, no_update
from pytz import timezone

from utils.colors import get_color
from utils.data_parsing import (
    annotate_events_with_flags,
    assign_event_rows,
    filter_week_events,
)

from ..plotting import generate_day_view_html
from ..utils import offer_type_emoji

PDT = timezone("America/Los_Angeles")


def register_callbacks(app, df):
    @app.callback(
        Output("overflow-box", "className"),
        Output("overflow-toggle", "children"),
        Input("overflow-toggle", "n_clicks"),
        State("overflow-date", "data"),
        prevent_initial_call=True,
    )
    def toggle_overflow(n_clicks, start_date_str):
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
        prevent_initial_call=True,
    )
    def show_event_modal(
        day_click,
        close_clicks,
        timer_tick,
        close_day_clicks,
        grid_clicks,
        day_column_clicks,
        week_offset,
        screen_width,
    ):
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

            if idx is None:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                )

            today = datetime.now(PDT)
            current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
            week_start = current_sunday + timedelta(weeks=week_offset)

            df_week = filter_week_events(df, week_start, week_start + timedelta(days=7))
            df_annot = annotate_events_with_flags(
                df_week, week_start, week_start + timedelta(days=7)
            )
            df_assigned = assign_event_rows(df_annot, week_start)
            df_assigned = df_assigned.drop_duplicates("orig_index")
            df_assigned = df_assigned.set_index("orig_index")

            if idx not in df_assigned.index:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                )

            row = df_assigned.loc[idx]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]

            rows: List[Any] = []
            emoji = offer_type_emoji(row.get("OfferType", ""))
            rows.append(
                html.H2(f"{emoji} Promo Info {emoji}", className="event-label-title")
            )

            for label in [
                "EventName",
                "Casino",
                "OfferType",
                "StartDate",
                "EndDate",
                "Offer",
            ]:
                if label in row:
                    display_label = {
                        "EventName": "Name of Event",
                        "StartDate": "Start of Event",
                        "EndDate": "End of Event",
                        "OfferType": "Offer Type",
                    }.get(label, label)

                    value = row[label]

                    if label in ["StartDate", "EndDate"]:
                        try:
                            value = pd.to_datetime(value).strftime(
                                "%b %d, %Y @ %I:%M %p"
                            )
                        except Exception:
                            pass

                    rows.append(
                        html.Div(
                            [
                                html.Strong(f"{display_label}: "),
                                html.Span(value),
                            ],
                            className="event-label",
                        )
                    )
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

            clicked_date = PDT.localize(datetime.strptime(date_str, "%Y-%m-%d"))
            content = generate_day_view_html(df, clicked_date, get_color, screen_width)

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

                today = datetime.now(PDT)
                current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
                week_start = current_sunday + timedelta(weeks=week_offset)
                clicked_date = week_start + timedelta(days=day_index)
                content = generate_day_view_html(
                    df, clicked_date, get_color, screen_width
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
                emoji = offer_type_emoji(data.get("OfferType", ""))
                rows = [
                    html.H2(
                        f"{emoji} Promo Info {emoji}", className="event-label-title"
                    )
                ]
                for label in [
                    "EventName",
                    "Casino",
                    "OfferType",
                    "StartDate",
                    "EndDate",
                    "Offer",
                ]:
                    if label in data:
                        display_label = {
                            "EventName": "Name of Event",
                            "StartDate": "Start of Event",
                            "EndDate": "End of Event",
                            "OfferType": "Offer Type",
                        }.get(label, label)

                        value = data[label]

                        if label in ["StartDate", "EndDate"]:
                            try:
                                value = pd.to_datetime(value).strftime(
                                    "%b %d, %Y @ %I:%M %p"
                                )
                            except Exception:
                                pass

                        rows.append(
                            html.Div(
                                [
                                    html.Strong(f"{display_label}: "),
                                    html.Span(value),
                                ],
                                className="event-label",
                            )
                        )
                return ({}, "modal show", rows, 0, {"display": "none"}, "", "")

        raise dash.exceptions.PreventUpdate
