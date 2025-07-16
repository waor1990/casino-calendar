from datetime import datetime, timedelta
from uuid import uuid4

import dash
from dash import Input, Output, State, html
from pytz import timezone

from ..utils import filter_long_spanning_events
from ..week_grid_layout import render_week_grid

PDT = timezone("America/Los_Angeles")


def register_callbacks(app, df):
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

    @app.callback(Output("week-label", "children"), Input("week-offset", "data"))
    def update_week_label(week_offset):
        today = datetime.now(PDT)
        current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        week_start = current_sunday + timedelta(weeks=week_offset)
        return (
            f"Events for the Week of {week_start.strftime('%B %d')} - "
            f"{(week_start + timedelta(days=6)).strftime('%B %d, %Y')}"
        )

    @app.callback(
        Output("week-offset", "data"),
        Output("prev-button", "disabled"),
        Output("next-button", "disabled"),
        Output("next-button", "title"),
        Input("prev-button", "n_clicks"),
        Input("next-button", "n_clicks"),
        State("week-offset", "data"),
    )
    def update_week_offset(_prev_clicks, _next_clicks, current_offset):
        ctx = dash.callback_context
        desired_offset = current_offset

        if ctx.triggered_id == "prev-button":
            desired_offset -= 1
        elif ctx.triggered_id == "next-button":
            desired_offset += 1

        desired_offset = max(-6, desired_offset)
        today = datetime.now(PDT)
        current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)

        next_week_offset = desired_offset + 1
        next_week_start = current_sunday + timedelta(weeks=next_week_offset)
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
        Output("week-chart-container", "children"),
        Output("overflow-date", "data"),
        Output("animation-refresh", "data"),
        Output("calendar-scroll-body", "style"),
        Input("usable-height", "data"),
        Input("week-offset", "data"),
        Input("screen-width", "data"),
        prevent_initial_call=True,
    )
    def render_single_week_chart(usable_height, week_offset, screen_width):
        today = datetime.now(PDT)
        current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        week_start = current_sunday + timedelta(weeks=week_offset)

        grid = render_week_grid(week_start, df, screen_width)

        week_end = week_start + timedelta(days=7)
        overflow_df = filter_long_spanning_events(df, week_start, week_end)

        if not overflow_df.empty:
            overflow_toggle = html.Button(
                f"\U0001f300 Show Ongoing Events for {week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}",
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
                        className="font-bold mb-section",
                        style={"color": "#6A5ACD", "display": "block"},
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

        chart = html.Div(
            children=[grid, overflow_toggle, overflow_box],
            id=f"week-chart-{week_offset}",
            className="slide-in week-chart-scroll",
            **{"data-week": week_offset},
        )

        style = (
            {"height": f"{usable_height}px"}
            if screen_width >= 768
            else {"minHeight": f"{usable_height}px"}
        )

        return chart, week_start.strftime("%Y-%m-%d"), str(uuid4()), style

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
