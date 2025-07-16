from datetime import datetime, timedelta
from math import floor
from typing import Callable, List, Tuple

import pandas as pd
import plotly.graph_objs as go
from dash import dcc, html

from utils.colors import get_color

from .utils import PDT, offer_type_emoji, trim_label


# Layout config shared across functions
def get_layout_config(screen_width: int) -> Tuple[int, int]:
    """Return hour height and label column width based on ``screen_width``."""

    hour_height = 20 if screen_width < 480 else 36 if screen_width < 768 else 44
    label_column_pct = 10
    return hour_height, label_column_pct


# Generate a responsive 24-hour vertical day view with absolutely positioned event blocks.
def generate_day_view_html(
    events_df: pd.DataFrame,
    clicked_date: datetime,
    get_color_fn: Callable[[], dict],
    screen_width: int = 1024,
) -> List[html.Div | dcc.Graph]:
    """Return a list of HTML elements representing a single day's events."""

    hour_height, label_column_pct = get_layout_config(screen_width)

    # Normalize clicked_date
    day_start = clicked_date.astimezone(PDT).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    day_end = day_start + timedelta(days=1)

    # Filter events strictly within the day
    events = events_df.copy()
    events["StartDate"] = pd.to_datetime(events["StartDate"]).dt.tz_convert(PDT)
    events["EndDate"] = pd.to_datetime(events["EndDate"]).dt.tz_convert(PDT)
    events = events[(events["StartDate"] >= day_start) & (events["EndDate"] <= day_end)]

    day_label = clicked_date.strftime("%A, %B %d")
    header_text = f"Events for {day_label}"

    if events.empty:
        return [
            html.H2(header_text, className="day-label day-modal-title"),
            html.Div("No events scheduled.", className="no-events"),
        ]

    # Time math
    events["start_offset_min"] = (
        events["StartDate"] - day_start
    ).dt.total_seconds() / 60
    events["end_offset_min"] = (events["EndDate"] - day_start).dt.total_seconds() / 60
    events["duration_min"] = events["end_offset_min"] - events["start_offset_min"]
    events = events.sort_values(by=["start_offset_min", "duration_min"])

    # Assign tracks dynamically to avoid overlap
    tracks = []
    track_assignments = []

    for _, event in events.iterrows():
        placed = False
        for i, track in enumerate(tracks):
            if all(
                event["start_offset_min"] >= t[1] or event["end_offset_min"] <= t[0]
                for t in track
            ):
                track.append((event["start_offset_min"], event["end_offset_min"]))
                track_assignments.append(i)
                placed = True
                break
        if not placed:
            tracks.append([(event["start_offset_min"], event["end_offset_min"])])
            track_assignments.append(len(tracks) - 1)

    events["overlap_index"] = track_assignments
    n_tracks = max(len(tracks), 1)
    width_pct = (100 - label_column_pct) / n_tracks

    color_map = get_color_fn()
    hour_blocks = []
    hour_lines = []
    event_blocks = []
    click_markers = []

    for hour in range(24):
        top_px = hour * hour_height
        label = (
            datetime(2000, 1, 1, hour).strftime("%I %p").lstrip("0")
            if hour % 3 == 0
            else ""
        )

        # Label on left
        hour_blocks.append(
            html.Div(
                label,
                className="hour-label",
                style={
                    "top": f"{top_px}px",
                    "height": f"{hour_height}px",
                    "width": f"{label_column_pct}%",
                },
            )
        )
        hour_lines.append(
            html.Div(
                className="hour-grid-line",
                style={
                    "top": f"{top_px}px",
                    "height": f"{hour_height}px",
                },
            )
        )

    # Event blocks + invisible click markers
    for _, row in events.iterrows():
        top_px = row["start_offset_min"] / 60 * hour_height
        height_px = max(24, row["duration_min"] / 60 * hour_height)
        left_pct = label_column_pct + row["overlap_index"] * width_pct

        colors = color_map.get(row["Casino"], {"bg": "#aaa", "text": "#000"})
        emoji = offer_type_emoji(row.get("OfferType", ""))

        short_span = row["duration_min"] < 90

        label_content = emoji if short_span else row["EventName"]
        children = [html.Span(label_content, className="event-block-day_text")]

        block_classes = ["event-block-day"]
        if short_span:
            block_classes.append("short-span")

        def _fmt_time(ts: pd.Timestamp) -> str:
            """Return timestamp formatted as h:mm AM/PM without leading zero."""
            return ts.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")

        tooltip = (
            f"{row['EventName']} ({row['Casino']}) - "
            f"{_fmt_time(row['StartDate'])} to {_fmt_time(row['EndDate'])}"
        )

        block_kwargs = dict(
            title=row["EventName"],
            className=" ".join(block_classes),
            style={
                "top": f"{top_px}px",
                "left": f"{left_pct}%",
                "width": f"{width_pct}%",
                "height": f"{height_px}px",
                "--bg": colors["bg"],
                "--fg": colors["text"],
            },
            **{"data-tooltip": tooltip},
        )

        # Visible block
        event_blocks.append(html.Div(children, **block_kwargs))

        # Invisible click marker for modal
        center_y = top_px + height_px / 2
        center_x = left_pct + width_pct / 2
        event_data = row[
            [
                "EventName",
                "Casino",
                "OfferType",
                "StartDate",
                "EndDate",
                "Offer",
            ]
        ].to_dict()

        click_markers.append(
            go.Scatter(
                x=[center_x / 100],
                y=[center_y],
                mode="markers",
                marker=dict(size=30, opacity=0.001, color="rgba(255,255,255,0.01)"),
                customdata=[[event_data]],
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # Clickable overlay graph
    click_graph = dcc.Graph(
        id="day-event-catcher",
        className="day-event-catcher",
        figure=go.Figure(
            data=click_markers,
            layout=go.Layout(
                clickmode="event+select",
                xaxis=dict(visible=False, range=[0, 1], fixedrange=True),
                yaxis=dict(visible=False, range=[0, 24 * hour_height], fixedrange=True),
                margin=dict(l=0, r=0, t=0, b=0),
                height=24 * hour_height,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            ),
        ),
        style={"height": f"{24 * hour_height}px"},
        config={"displayModeBar": False},
    )

    # Sticky Add day label + scrollable grid container
    header = html.H2(
        header_text,
        className="day-label day-modal-title",
    )

    return [
        header,
        html.Div(
            children=hour_blocks + hour_lines + event_blocks + [click_graph],
            className="day-grid",
            style={
                "height": f"{24 * hour_height}px",
            },
        ),
    ]


def build_weekly_figure(events_df, screen_width, week_start):
    """Return the legacy Plotly weekly figure.

    This helper is retained for test coverage and reference while the
    application uses a CSS grid for rendering.
    """

    font_rem = (
        12
        if screen_width < 480
        else 14 if screen_width < 768 else 16 if screen_width < 1024 else 18
    )
    event_font_size_px = font_rem * 1

    shapes = []
    annotations = []
    hover_markers = []

    ARROW_OFFSET = 0.1
    PADDING = 0.1
    slot_height = 0.5
    slot_padding = 0.075
    row_unit_height = slot_height + slot_padding
    MIN_ROWS = 5

    used_rows_by_day = {i: set() for i in range(7)}
    recurring_rows = {}
    row_nums = []
    current_row = 0

    tick_labels = [
        (week_start + timedelta(days=i)).strftime("%a")
        + "<br>"
        + (week_start + timedelta(days=i)).strftime("%b %d")
        for i in range(7)
    ]

    for i in range(1, 7):
        shapes.append(
            dict(
                type="line",
                x0=i,
                x1=i,
                y0=-0.5,
                y1=100,  # placeholder; replaced later
                line=dict(color="black", width=1),
                layer="below",
            )
        )

    grouped = events_df.copy()

    casino_colors = get_color()

    for priority in sorted(grouped["overflow_sort"].unique()):
        group_df = grouped[grouped["overflow_sort"] == priority]
        group_df = group_df.sort_values(
            by=["StartDate", "EndDate", "Duration", "Casino"],
            ascending=[True, True, False, True],
        )

        for idx, row in group_df.iterrows():
            start_delta = (row["StartDate"] - week_start).total_seconds() / (24 * 3600)
            end_delta = (row["EndDate"] - week_start).total_seconds() / (24 * 3600)

            visible_start = max(start_delta, 0)
            visible_end = min(end_delta, 7)
            start_day = max(0, floor(visible_start))
            end_day = min(6, floor(visible_end - 1e-6))

            recurring_key = f"{row['EventName']}|{row['Casino']}|{row['StartDate'].time()}|{row['EndDate'].time()}"
            preferred_row = recurring_rows.get(recurring_key)
            row_assigned = False

            if preferred_row is not None and all(
                preferred_row not in used_rows_by_day[d]
                for d in range(start_day, end_day + 1)
            ):
                assigned_row = preferred_row
                row_assigned = True
            else:
                for r in range(current_row, 100):
                    if all(
                        r not in used_rows_by_day[d]
                        for d in range(start_day, end_day + 1)
                    ):
                        assigned_row = r
                        recurring_rows[recurring_key] = r
                        row_assigned = True
                        break

            if row_assigned:
                for d in range(start_day, end_day + 1):
                    used_rows_by_day[d].add(assigned_row)
                row_nums.append(assigned_row)

            row_num = assigned_row
            y_center = (row_num + 0.5) * row_unit_height

            adjusted_start = 0 + PADDING if row["has_left_arrow"] else visible_start
            adjusted_end = 7 - PADDING if row["has_right_arrow"] else visible_end
            block_width = adjusted_end - adjusted_start

            approx_char_px = event_font_size_px * 0.6
            block_px = screen_width * (block_width / 7) * 0.95
            max_chars = max(int(block_px / approx_char_px), 0)

            label = row["EventName"]
            trimmed_label = trim_label(label, max_chars, row.get("OfferType", ""))

            color = casino_colors[row["Casino"]]["bg"]
            text_color = casino_colors[row["Casino"]]["text"]

            shapes.append(
                dict(
                    type="rect",
                    x0=adjusted_start,
                    x1=adjusted_end,
                    y0=y_center - slot_height / 2,
                    y1=y_center + slot_height / 2,
                    fillcolor=color,
                    line=dict(color="black", width=1),
                    layer="above",
                )
            )

            if row["has_left_arrow"]:
                shapes.append(
                    dict(
                        type="path",
                        path=f"M 0,{y_center} L{ARROW_OFFSET},{y_center + 0.2} L{ARROW_OFFSET},{y_center - 0.2} Z",
                        fillcolor="black",
                        line=dict(color="black", width=1),
                        layer="above",
                    )
                )

            if row["has_right_arrow"]:
                shapes.append(
                    dict(
                        type="path",
                        path=f"M 7,{y_center} L{7 - ARROW_OFFSET},{y_center + 0.2} L{7 - ARROW_OFFSET},{y_center - 0.2} Z",
                        fillcolor="black",
                        line=dict(color="black", width=1),
                        layer="above",
                    )
                )

            annotations.append(
                dict(
                    x=(adjusted_start + adjusted_end) / 2,
                    y=y_center,
                    text=trimmed_label,
                    showarrow=False,
                    font=dict(size=event_font_size_px, color=text_color),
                    xanchor="center",
                    yanchor="middle",
                )
            )

            hover_markers.append(
                go.Scatter(
                    x=[(adjusted_start + adjusted_end) / 2],
                    y=[y_center],
                    text=[label],
                    mode="markers",
                    marker=dict(size=30, opacity=0.2),
                    hoverinfo="text",
                    showlegend=False,
                    customdata=[[row.to_dict()]],
                )
            )

        current_row = max(row_nums, default=current_row) + 1

    total_rows = max(row_nums, default=0)
    adjusted_rows = max(MIN_ROWS, total_rows)
    base_y_top = adjusted_rows * row_unit_height + 0.5
    chart_height = int(base_y_top * 40)

    for shape in shapes:
        if shape["type"] == "line":
            shape["y1"] = base_y_top

    for day_index in range(7):
        hover_markers.append(
            go.Scatter(
                x=[day_index + 0.5],
                y=[base_y_top + 0.5],
                mode="markers",
                marker=dict(size=20, opacity=0.2),
                hoverinfo="text",
                hovertext=["View Day's Events"],
                customdata=[[{"type": "day_click", "day_index": day_index}]],
                showlegend=False,
                name="",
            )
        )

    return go.Figure(
        data=hover_markers,
        layout=go.Layout(
            clickmode="event+select",
            shapes=shapes,
            annotations=annotations,
            xaxis=dict(
                type="linear",
                tickmode="array",
                tickvals=[i + 0.5 for i in range(7)],
                ticktext=[
                    f"<b style='color:#00008B;font-size:{event_font_size_px}px'>{label}</b>"
                    for label in tick_labels
                ],
                side="top",
                showgrid=True,
                gridcolor="lightgray",
                zeroline=False,
                range=[0, 7],
                fixedrange=True,
            ),
            yaxis=dict(
                range=[-0.5, base_y_top + 0.5],
                showgrid=False,
                visible=False,
                fixedrange=True,
            ),
            height=chart_height,
            margin=dict(t=40, b=20, l=20, r=20),
        ),
    )
