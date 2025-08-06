from datetime import datetime, timedelta
from math import floor
from typing import Any, Callable, List, Tuple

import pandas as pd
import plotly.graph_objs as go
from dash import dcc, html
from utils.colors import get_color

from .utils import (
    filter_long_spanning_events,
    offer_type_emoji,
    to_naive_utc,
    to_pdt,
    trim_label,
)

# Constants used to size the day modal dynamically
DAY_MODAL_MIN_REM = 18
# Extra width when only a few events are shown
DAY_MODAL_WIDE_REM = 24
DAY_MODAL_LABEL_REM = 3
DAY_MODAL_TRACK_REM = 7


# Layout config shared across functions
def get_layout_config(screen_width: int) -> Tuple[int, int]:
    """Return hour height and label column width based on ``screen_width``."""

    # Reduce hour height to fit all 24 hours within modal height
    hour_height = 16 if screen_width < 480 else 20 if screen_width < 768 else 24
    label_column_pct = 12  # Slightly wider for better hour label visibility
    return hour_height, label_column_pct


# Generate a responsive 24-hour vertical day view with absolutely positioned event blocks.
def generate_day_view_html(
    events_df: pd.DataFrame,
    clicked_date: datetime,
    get_color_fn: Callable[[], dict],
    screen_width: int = 1024,
) -> List[html.Div | dcc.Graph | html.H2]:
    """Return a list of HTML elements representing a single day's events."""

    hour_height, _ = get_layout_config(screen_width)

    # Normalize clicked_date
    # The clicked_date comes from the callback as naive UTC (via to_naive_utc)
    # We need to treat it as a local PDT date for day boundaries
    if clicked_date.tzinfo is None:
        # Treat the naive UTC date as a local PDT date for day boundaries
        from pytz import timezone

        PDT = timezone("America/Los_Angeles")
        day_start = PDT.localize(
            clicked_date.replace(hour=0, minute=0, second=0, microsecond=0)
        )
    else:
        day_start = to_pdt(clicked_date).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    day_end = day_start + timedelta(days=1)

    # Filter events that overlap with the day
    # Show any event that either starts, ends, or spans through the current day
    # BUT exclude ongoing events that are shown in the overflow box
    events = events_df.copy()
    events["StartDate"] = pd.to_datetime(events["StartDate"]).map(to_pdt)
    events["EndDate"] = pd.to_datetime(events["EndDate"]).map(to_pdt)

    # Calculate week boundaries to identify ongoing events
    # Find the week that contains the clicked day
    days_from_sunday = day_start.weekday() + 1  # Monday=1, Sunday=0
    if days_from_sunday == 7:  # Sunday
        days_from_sunday = 0
    week_start = day_start - timedelta(days=days_from_sunday)
    week_end = week_start + timedelta(days=7)

    # Get ongoing events for this week (events that span the entire week)
    ongoing_events = filter_long_spanning_events(
        events_df, to_naive_utc(week_start), to_naive_utc(week_end)
    )
    ongoing_event_ids = set(ongoing_events.index) if not ongoing_events.empty else set()

    # Filter events that either start or end on the selected day
    # Include events that:
    # 1. End after or at day start AND start before day end (overlap with day)
    # 2. Are not ongoing events (shown in overflow box)
    # 3. Don't start too far before or end too far after (reasonable time window)

    # Define time window: allow events within a reasonable range of the day
    # This prevents very distant events from cluttering the day view while still
    # showing events that meaningfully overlap with the selected day
    earliest_start = day_start - timedelta(
        days=2
    )  # Allow events starting up to 2 days before
    latest_end = day_end + timedelta(days=2)  # Allow events ending up to 2 days after

    events = events[
        (
            events["EndDate"] >= day_start
        )  # Event ends at or after day starts (includes boundary)
        & (events["StartDate"] < day_end)  # Event starts before day ends
        & (events["StartDate"] >= earliest_start)  # Event doesn't start too early
        & (events["EndDate"] <= latest_end)  # Event doesn't end too late
        & (~events.index.isin(ongoing_event_ids))  # Exclude ongoing events
    ]

    day_label = to_pdt(clicked_date).strftime("%A, %B %d")
    header_text = f"Events for {day_label}"

    if events.empty:
        placeholder_graph = dcc.Graph(
            id="day-event-catcher",
            figure=go.Figure(),
            config={"displayModeBar": False},
            style={"display": "none"},
        )

        return [
            html.H2(header_text, className="day-label day-modal-title"),
            html.Div("No events scheduled.", className="no-events"),
            placeholder_graph,
        ]

    # Time math - clip events to day boundaries
    events["adj_start"] = events["StartDate"].where(
        events["StartDate"] >= day_start, day_start
    )
    events["adj_start"] = events["adj_start"].where(
        events["adj_start"] <= day_end, day_end
    )
    events["adj_end"] = events["EndDate"].where(
        events["EndDate"] >= day_start, day_start
    )
    events["adj_end"] = events["adj_end"].where(events["adj_end"] <= day_end, day_end)
    events["start_offset_min"] = (
        events["adj_start"] - day_start
    ).dt.total_seconds() / 60
    events["end_offset_min"] = (events["adj_end"] - day_start).dt.total_seconds() / 60
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

    # Calculate grid sizing before positioning blocks - make more compact
    min_width_rem = DAY_MODAL_WIDE_REM if len(events) < 5 else DAY_MODAL_MIN_REM
    max_name_len = max((len(str(n)) for n in events["EventName"]), default=0)
    char_rem = 0.4  # Reduced from 0.55 for more compact layout
    # Use smaller track width calculation for tighter spacing
    track_width = max(4, min(6, max_name_len * char_rem))  # 4-6rem per track
    label_and_names = DAY_MODAL_LABEL_REM + track_width * n_tracks
    grid_min_width = max(
        min_width_rem,
        label_and_names,
    )

    label_column_pct = DAY_MODAL_LABEL_REM / grid_min_width * 100
    width_pct = (100 - label_column_pct) / n_tracks

    color_map = get_color_fn()
    hour_blocks = []
    hour_lines = []
    event_blocks = []
    click_markers = []

    for hour in range(24):
        top_px = hour * hour_height
        # Show hour labels every 3 hours to avoid clutter
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

        # Grid line spanning the full width
        hour_lines.append(
            html.Div(
                className="hour-grid-line",
                style={
                    "top": f"{top_px}px",
                    "left": f"{label_column_pct}%",
                    "width": f"{100 - label_column_pct}%",
                },
            )
        )  # Event blocks + invisible click markers
    for _, row in events.iterrows():
        top_px = row["start_offset_min"] / 60 * hour_height
        height_px = max(16, row["duration_min"] / 60 * hour_height)
        # Position blocks using proper track-based layout to prevent overlap
        left_pct = label_column_pct + row["overlap_index"] * width_pct

        colors = color_map.get(row["Casino"], {"bg": "#aaa", "text": "#000"})
        emoji = offer_type_emoji(row.get("OfferType", ""))

        short_span = row["duration_min"] < 90

        if short_span:
            children = [html.Span(emoji, className="event-block-day-text")]
        else:
            # Approximate number of text lines that can fit in the block
            line_height = 18
            max_lines = max(1, int(height_px // line_height))

            values = [
                str(row["EventName"]),
                str(row["Casino"]),
                str(row.get("Offer", "")),
                emoji,
            ]

            lines = [
                html.Span(v, className="event-block-day-line")
                for v in values[:max_lines]
                if v
            ]

            children = html.Div(lines, className="event-block-day-text")

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

        # Calculate appropriate width based on content and available track space
        event_name = str(row["EventName"])
        casino_name = str(row["Casino"])

        # Calculate maximum width based on track allocation (leaving small margin)
        track_width_pct = width_pct * 0.9  # Use 90% of track to leave margin
        max_track_width = f"{track_width_pct}%"

        # Build the style dictionary with base properties
        style_dict = {
            "top": f"{top_px}px",
            "left": f"{left_pct}%",
            "height": f"{height_px}px",
            "--bg": colors["bg"],
            "--fg": colors["text"],
        }

        if short_span:
            # For short events, use character-based width when there are few events
            if len(events) < 5:  # Few events - use character-based width
                char_width = f"{len(event_name) + 2}ch"
                style_dict["width"] = "auto"
                style_dict["minWidth"] = char_width
                style_dict["maxWidth"] = min(char_width, max_track_width)
            else:
                # Many events - use minimal width based on emoji
                style_dict["width"] = "auto"
                style_dict["minWidth"] = "2.5rem"
                style_dict["maxWidth"] = min(
                    "3rem", max_track_width
                )  # Constrain to track
        else:
            # For longer events, use auto width with both character and track constraints
            char_min = f"{min(len(event_name), len(casino_name))}ch"
            char_max = (
                f"{max(len(event_name), len(casino_name)) + 1}ch"  # Reduced padding
            )

            style_dict["width"] = "auto"
            style_dict["minWidth"] = char_min
            style_dict["maxWidth"] = (
                f"min({char_max}, {max_track_width})"  # Respect track bounds
            )

        block_kwargs: dict[str, Any] = dict(
            title=row["EventName"],
            className=" ".join(block_classes),
            style=style_dict,
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
                "minWidth": f"{grid_min_width}rem",
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
