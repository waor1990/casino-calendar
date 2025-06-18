# isort:skip_file


def register_callbacks(app):
    from datetime import datetime, timedelta
    from typing import Any, List

    import dash
    import pandas as pd
    from dash import ALL, Input, Output, State, dcc, html, no_update
    from pytz import timezone

    from .data import load_event_data
    from .plotting import generate_day_view_html, generate_weekly_view, get_color
    from .week_grid_layout import render_week_grid

    PDT = timezone("America/Los_Angeles")
    df = load_event_data()

    # Screen detection JS (for height + width)
    app.clientside_callback(
        """
        function(n_intervals) {
            const width = window.innerWidth;
            const height = window.innerHeight;

            const header = document.getElementById("app-header");
            const headerHeight = header ? header.offsetHeight : 100;

            const usable = Math.max(height - headerHeight - 20, 300);
            return [width, usable];
        }
        """,
        Output("screen-width", "data"),
        Output("usable-height", "data"),
        Input("initial-trigger", "n_intervals"),
    )

    # Sticky header with responsive legend
    @app.callback(Output("week-label", "children"), Input("week-offset", "data"))
    def update_week_label(week_offset):
        today = datetime.now(PDT)
        current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        week_start = current_sunday + timedelta(weeks=week_offset)

        return f"Events for the Week of {week_start.strftime('%B %d')} - {(week_start + timedelta(days=6)).strftime('%B %d, %Y')}"

    # Update week offset on button clicks
    @app.callback(
        Output("week-offset", "data"),
        Output("prev-button", "disabled"),
        Output("next-button", "disabled"),
        Output("next-button", "title"),
        Input("prev-button", "n_clicks"),
        Input("next-button", "n_clicks"),
        State("week-offset", "data"),
    )
    def update_week_offset(prev_clicks, next_clicks, current_offset):
        ctx = dash.callback_context
        desired_offset = current_offset

        if ctx.triggered_id == "prev-button":
            desired_offset -= 1
        elif ctx.triggered_id == "next-button":
            desired_offset += 1

        # Limit going back no more than 6 weeks
        desired_offset = max(-6, desired_offset)
        # Limit forward navigation if next 4 weeks are empty
        today = datetime.now(PDT)
        current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)

        next_week_offset = desired_offset + 1
        next_week_start = current_sunday + timedelta(weeks=next_week_offset)
        next_week_end = next_week_start + timedelta(days=6)

        has_next_week_events = not df[
            (df["EndDate"] > next_week_start) & (df["StartDate"] < next_week_end)
        ].empty

        if not has_next_week_events and desired_offset > current_offset:
            desired_offset = current_offset

        prev_disabled = desired_offset <= -6
        next_disabled = not has_next_week_events

        # Dynamic tooltip text for forward navigation
        next_title = "No Upcoming events" if next_disabled else "Upcoming Week"

        return desired_offset, prev_disabled, next_disabled, next_title

    @app.callback(
        Output("show-css-grid", "data"),
        Output("preview-grid-button", "children"),
        Input("preview-grid-button", "n_clicks"),
        State("show-css-grid", "data"),
        prevent_initial_call=True,
    )
    def toggle_css_grid(n_clicks, current_state):
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate

        new_state = not current_state
        label = "Hide CSS Layout" if new_state else "Show CSS Layout"
        return new_state, label

    @app.callback(
        Output("dev-preview-output", "children"),
        Input("week-offset", "data"),
        Input("show-css-grid", "data"),
        Input("screen-width", "data"),
        prevent_initial_call=True,
    )
    def show_dev_preview(week_offset, show_grid, screen_width):
        if not show_grid:
            return html.Div()

        today = datetime.now(PDT)
        current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        week_start = current_sunday + timedelta(weeks=week_offset)

        grid = render_week_grid(week_start, df, screen_width)

        return html.Div(
            grid,
            id=f"week-grid-{week_offset}",
            className="slide-in week-chart-scroll",
        )

    @app.callback(
        Output("show-plotly-grid", "data"),
        Output("plotly-grid-button", "children"),
        Input("plotly-grid-button", "n_clicks"),
        State("show-plotly-grid", "data"),
        prevent_initial_call=True,
    )
    def toggle_plotly_grid(n_clicks, current_state):
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate

        new_state = not current_state
        button_label = "Hide Plotly Layout" if new_state else "Show Plotly Layout"
        return new_state, button_label

    @app.callback(
        Output("week-chart-container", "children"),
        Output("overflow-date", "data"),
        Output("animation-refresh", "data"),
        Input("usable-height", "data"),
        Input("week-offset", "data"),
        Input("screen-width", "data"),
        Input("show-plotly-grid", "data"),
        prevent_initial_call=True,
    )
    def render_single_week_chart(usable_height, week_offset, screen_width, show_chart):
        today = datetime.now(PDT)
        current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        week_start = current_sunday + timedelta(weeks=week_offset)

        if not show_chart:
            import plotly.graph_objs as go

            hidden_graph = dcc.Graph(
                id="weekly-graph",
                figure=go.Figure(),
                config={"displayModeBar": False},
                style={"display": "none"},
            )

            container = html.Div(
                children=[hidden_graph],
                id=f"week-chart-{week_offset}",
                style={"display": "none"},
            )

            from uuid import uuid4

            return container, week_start.strftime("%Y-%m-%d"), str(uuid4())

        fig, overflow_df = generate_weekly_view(week_start, df, screen_width)

        end_date = week_start + timedelta(days=6)

        # Overflow content toggle & box
        if not overflow_df.empty:
            overflow_toggle = html.Button(
                f"🌀 Show Ongoing Events for {week_start.strftime('%b %d')} - {end_date.strftime('%b %d')}",
                id="overflow-toggle",
                n_clicks=0,
                className="overflow-toggle",
            )

            overflow_box = html.Div(
                id="overflow-box",
                className="overflow-box-expand",
                children=[
                    html.Strong(
                        "Ongoing Events This Week:",
                        style={
                            "color": "#6A5ACD",
                            "display": "block",
                            "marginBottom": "8px",
                        },
                    ),
                    html.Ul(
                        [
                            html.Li(
                                f"{row['EventName']} ({row['Casino']}) - {row['StartDate'].strftime('%b %d')} to {row['EndDate'].strftime('%b %d')}",
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

        # Shared scrollable container for graph + overflow
        chart = html.Div(
            children=[
                dcc.Graph(
                    id="weekly-graph",
                    figure=fig,
                    config={"displayModeBar": False},
                    style={"width": "100%", "height": "auto"},
                ),
                overflow_toggle,
                overflow_box,
            ],
            id=f"week-chart-{week_offset}",
            className="slide-in week-chart-scroll",
            style={"height": f"{usable_height}px"},
            **{"data-week": week_offset},
        )

        from uuid import uuid4

        return chart, week_start.strftime("%Y-%m-%d"), str(uuid4())

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
            f"🌀 Hide Ongoing Events for {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
            if is_open
            else f"🌀 Show Ongoing Events for {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
        )

        return box_class, button_text

    @app.callback(
        Output("event-modal", "style"),
        Output("event-modal", "className"),
        Output("event-modal-body", "children"),
        Output("close-timer", "n_intervals"),
        Output("weekly-graph", "clickData"),
        Output("day-modal", "style"),
        Output("day-modal", "className"),
        Output("day-modal-body", "children"),
        Input("weekly-graph", "clickData"),
        Input("day-event-catcher", "clickData"),
        Input("close-modal", "n_clicks"),
        Input("close-timer", "n_intervals"),
        Input("close-day-modal", "n_clicks"),
        Input({"type": "grid-event", "index": ALL}, "n_clicks"),
        State("week-offset", "data"),
        State("screen-width", "data"),
        prevent_initial_call=True,
    )
    def show_event_modal(
        weekly_click,
        day_click,
        close_clicks,
        timer_tick,
        close_day_clicks,
        grid_clicks,
        week_offset,
        screen_width,
    ):
        ctx = dash.callback_context
        triggered_id = ctx.triggered_id

        if triggered_id == "close-timer":
            return no_update, "", "", 0, None, {"display": "none"}, "", ""

        if triggered_id == "close-modal":
            return (
                no_update,
                "modal closing",
                no_update,
                1,
                None,
                no_update,
                no_update,
                no_update,
            )

        if triggered_id == "close-day-modal":
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                None,
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
                    None,
                    no_update,
                    no_update,
                    no_update,
                )

            df2 = load_event_data()
            from .plotting import (
                annotate_events_with_flags,
                assign_event_rows,
                filter_week_events,
            )

            today = datetime.now(PDT)
            current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
            week_start = current_sunday + timedelta(weeks=week_offset)

            df_week = filter_week_events(
                df2, week_start, week_start + timedelta(days=7)
            )
            df_annot = annotate_events_with_flags(
                df_week, week_start, week_start + timedelta(days=7)
            )
            df_assigned = assign_event_rows(df_annot, week_start)
            df_assigned = df_assigned.set_index("orig_index")

            if idx not in df_assigned.index:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    None,
                    no_update,
                    no_update,
                    no_update,
                )

            row = df_assigned.loc[idx]

            rows: List[Any] = []
            # title
            rows.append(html.H2("Event Details", className="event-label-title"))

            for label in [
                "EventName",
                "Casino",
                "Location",
                "StartDate",
                "EndDate",
                "Offer",
            ]:
                if label in row:
                    display_label = {
                        "EventName": "Name of Event",
                        "StartDate": "Start of Event",
                        "EndDate": "End of Event",
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
                                html.Strong(
                                    f"{display_label}: ", style={"color": "#6A5ACD"}
                                ),
                                html.Span(value),
                            ],
                            className="event-label",
                        )
                    )
            return ({}, "modal show", rows, 0, None, {"display": "none"}, "", "")

        click_data = None
        if triggered_id == "weekly-graph":
            click_data = weekly_click
        elif triggered_id == "day-event-catcher":
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
                        None,
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
                    None,
                    {},
                    "modal show",
                    content,
                )

            if data and all(
                k in data
                for k in [
                    "EventName",
                    "Casino",
                    "Location",
                    "StartDate",
                    "EndDate",
                    "Offer",
                ]
            ):
                # Normal event click
                rows = [html.H2("Event Details", className="event-label-title")]
                for label in [
                    "EventName",
                    "Casino",
                    "Location",
                    "StartDate",
                    "EndDate",
                    "Offer",
                ]:
                    if label in data:
                        display_label = {
                            "EventName": "Name of Event",
                            "StartDate": "Start of Event",
                            "EndDate": "End of Event",
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
                                    html.Strong(
                                        f"{display_label}: ", style={"color": "#6A5ACD"}
                                    ),
                                    html.Span(value),
                                ],
                                className="event-label",
                            )
                        )
                return ({}, "modal show", rows, 0, None, {"display": "none"}, "", "")

        raise dash.exceptions.PreventUpdate

    # Re-trigger slide-in animation when week content is rendered
    app.clientside_callback(
        """
        function(refresh) {
            setTimeout(function() {
                const container = document.getElementById('week-chart-container');
                if (!container) { return; }
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
