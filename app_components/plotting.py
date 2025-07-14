from collections import defaultdict
from datetime import timedelta
from math import floor

import pandas as pd
import plotly.graph_objs as go
from dash import dcc, html

from .utils import PDT, offer_type_emoji


# Layout config shared across functions
def get_layout_config(screen_width):
    hour_height = 20 if screen_width < 480 else 36 if screen_width < 768 else 44
    label_column_pct = 10
    return hour_height, label_column_pct


# Color map by Casino
def get_color():
    color_map = {
        "ilani": {"bg": "#2c6f7f", "text": "#ffffff"},
        "Spirit Mountain Casino": {"bg": "#a74321", "text": "#ffffff"},
        "Lucky Eagle Casino": {"bg": "#862c8e", "text": "#ffffff"},
        "Muckleshoot Casino": {"bg": "#1e1c29", "text": "#ffffff"},
        "Little Creek Casino": {"bg": "#3086c3", "text": "#ffffff"},
        "Red Wind Casino": {"bg": "#e13332", "text": "#ffffff"},
        "Snoqualmie Casino": {"bg": "#00a9e0", "text": "#ffffff"},
        "Angel of the Winds Casino": {"bg": "#64c7cc", "text": "#ffffff"},
        "Lucky Dog Casino": {"bg": "#f07a22", "text": "#000000"},
        "Legends Casino": {"bg": "#ca9a41", "text": "#000000"},
        "Chinook Winds Casino": {"bg": "#32373d", "text": "#ffffff"},
        "Emerald Queen Casino": {"bg": "#d62e52", "text": "#ffffff"},
        "Rolling Hills Casino": {"bg": "#5b1d1e", "text": "#ffffff"},
        "Wildhorse Casino": {"bg": "#d21245", "text": "#ffffff"},
        "Tulalip Casino": {"bg": "#155e6d", "text": "#ffffff"},
        "Quil Ceda Creek Casino": {"bg": "#9a0709", "text": "#ffffff"},
        "Seven Feathers Casino": {"bg": "#41c5de", "text": "#000000"},
    }

    default_colors = {
        "#ff0000",
        "#00ff00",
        "#0000ff",
        "#ffff00",
        "#ff00ff",
        "#00ffff",
        "#ff8000",
        "#800000",
        "#008000",
        "#000080",
        "#800080",
        "#ffa500",
        "#808080",
        "#ff6347",
        "#ff4500",
        "#ff00ff",
        "#008080",
        "#4b0082",
        "#008b8b",
        "#000080",
        "#4682b4",
    }

    result = {}
    for casino, colors in color_map.items():
        result[casino] = colors

    if not result:
        dummy_casinos = [f"Casino {i}" for i in range(len(default_colors))]
        for casino_name, color in zip(dummy_casinos, default_colors):
            result[casino_name] = {"bg": color, "text": "#000000"}

    return result


# Add arrow indicators for events that span outside the week
def annotate_events_with_flags(events_df, week_start, week_end):
    events_df = events_df.copy()
    # Preserve the original index so CSS grid clicks can reference the global row
    events_df["orig_index"] = events_df.index

    # Add a duration column for sorting, and sort by: both left and right arrows, only left arrow, fully within week, and only right arrow
    events_df["Duration"] = (
        events_df["EndDate"] - events_df["StartDate"]
    ).dt.total_seconds()
    events_df["has_left_arrow"] = events_df["StartDate"] < week_start
    events_df["has_right_arrow"] = events_df["EndDate"] > week_end

    def get_overflow_priority(row):
        # Overflow priority: both arrows -> 0, right only -> 1, none -> 2, left only -> 3
        if row["has_left_arrow"] and row["has_right_arrow"]:
            return 0
        if row["has_right_arrow"]:
            return 3
        if not row["has_left_arrow"] and not row["has_right_arrow"]:
            return 2
        return 1  # left only

    events_df["overflow_sort"] = events_df.apply(get_overflow_priority, axis=1)

    # Sort events and drop the previous index, but keep the preserved orig_index column
    return events_df.sort_values(
        by=["overflow_sort", "StartDate", "EndDate", "Duration", "Casino"],
        ascending=[True, True, True, False, True],
    ).reset_index(drop=True)


# Filter events that overlap with the current week, excluding long_spanning events
def filter_week_events(events_df, week_start, week_end):
    return events_df[
        (events_df["EndDate"] > week_start)
        & (events_df["StartDate"] < week_end)
        & ~(events_df["StartDate"] == week_end)
        & ~((events_df["StartDate"] < week_start) & (events_df["EndDate"] > week_end))
    ].copy()


def assign_event_rows(events_df, week_start):
    # Layout params
    used_rows_by_day = {i: set() for i in range(7)}
    recurring_rows = defaultdict(int)
    current_row = 0
    row_nums = []

    for priority in sorted(events_df["overflow_sort"].unique()):
        group_df = events_df[events_df["overflow_sort"] == priority].sort_values(
            by=["StartDate", "EndDate", "Duration", "Casino"],
            ascending=[True, True, False, True],
        )

        for idx, row in group_df.iterrows():
            row = events_df.loc[idx]
            start_delta = (row["StartDate"] - week_start).total_seconds() / (24 * 3600)
            end_delta = (row["EndDate"] - week_start).total_seconds() / (24 * 3600)

            # Calculate the visible range of the event within the 7-day week
            visible_start = max(start_delta, 0)
            visible_end = min(end_delta, 7)

            start_day = max(0, floor(visible_start))
            end_day = min(6, floor(visible_end - 1e-6))

            recurring_key = f"{row['EventName']}|{row['Casino']}|{row['StartDate'].time()}|{row['EndDate'].time()}"
            preferred_row = recurring_rows.get(recurring_key)
            row_assigned = False

            # First try preferred row
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

            # If not usable, find a new row
            if row_assigned:
                for d in range(start_day, end_day + 1):
                    used_rows_by_day[d].add(assigned_row)
                events_df.at[idx, "row_num"] = assigned_row
                row_nums.append(assigned_row)

        current_row = max(row_nums, default=current_row) + 1

    return events_df


# Generate a responsive 24-hour vertical day view with absolutely positioned event blocks.
def generate_day_view_html(events_df, clicked_date, get_color_fn, screen_width=1024):
    hour_height, label_column_pct = get_layout_config(screen_width)

    # Normalize clicked_date
    day_start = clicked_date.astimezone(PDT).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    day_end = day_start + timedelta(days=1)

    # Filter events that overlap with the day window
    events = events_df.copy()
    events["StartDate"] = pd.to_datetime(events["StartDate"]).dt.tz_convert(PDT)
    events["EndDate"] = pd.to_datetime(events["EndDate"]).dt.tz_convert(PDT)
    events = events[(events["StartDate"] < day_end) & (events["EndDate"] > day_start)]

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
        label = f"{hour:02d}:00" if hour % 3 == 0 else ""

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
