from datetime import timedelta

import pandas as pd
import plotly.graph_objs as go
from dash import dcc, html

from .utils import PDT, offer_type_emoji


# Layout config shared across functions
def get_layout_config(screen_width):
    hour_height = 20 if screen_width < 480 else 36 if screen_width < 768 else 44
    label_column_pct = 10
    return hour_height, label_column_pct


# Generate a responsive 24-hour vertical day view with absolutely positioned event blocks.
def generate_day_view_html(events_df, clicked_date, get_color_fn, screen_width=1024):
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
