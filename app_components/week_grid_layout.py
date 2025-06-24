import pandas as pd
from dash import html

from .plotting import (
    annotate_events_with_flags,
    assign_event_rows,
    filter_week_events,
    get_color,
)
from .utils import get_week_range, trim_label


def render_week_grid(clicked_date, df, screen_width=1024):
    # Calculate week bounds
    week_start, week_end = get_week_range(clicked_date)
    dates = pd.date_range(week_start, periods=7)
    # Build 7 day-label divs for header row
    day_labels = []
    for i, date in enumerate(dates):
        day_labels.append(
            html.Div(
                children=[
                    html.Div(date.strftime("%a")),
                    html.Div(date.strftime("%b %d")),
                ],
                className="day-label-grid",
                style={"gridColumn": f"{i + 1}"},
            )
        )

    # Wrap the labels so the entire row can be sticky
    header_row = html.Div(day_labels, className="day-label-wrapper")

    # Filer/annotate/assign events
    df_week = filter_week_events(df, week_start, week_end)
    df_annot = annotate_events_with_flags(df_week, week_start, week_end)
    df_assigned = assign_event_rows(df_annot, week_start)
    colors = get_color()

    if df_assigned.empty:
        event_rows = 5
    else:
        max_row = df_assigned["row_num"].max()
        event_rows = int(max_row) + 1

    # Build CSS--grid event-block divs that are clickable
    event_blocks = []
    for idx, row in df_assigned.iterrows():
        delta_start = row["StartDate"] - week_start
        delta_end = row["EndDate"] - week_start
        start_delta = delta_start.total_seconds() / (24 * 3600)
        end_delta = delta_end.total_seconds() / (24 * 3600)

        visible_start = max(start_delta, 0)
        visible_end = min(end_delta, 7)

        row_num = row["row_num"] + 2

        duration_days = visible_end - visible_start

        # Percentage offsets for fractional placement
        left_pct = (visible_start / 7) * 100
        width_pct = (duration_days / 7) * 100

        # Trim label based on span width and screen size
        label = row["EventName"]
        font_px = (
            12
            if screen_width < 480
            else 14 if screen_width < 768 else 16 if screen_width < 1024 else 18
        )
        approx_char_px = font_px * 0.6
        block_px = screen_width * ((visible_end - visible_start) / 7) * 0.95
        max_chars = max(int(block_px / approx_char_px), 0)
        text = trim_label(label, max_chars, row.get("OfferType", ""))

        # Determine arrow classes
        cls = ["event-block-grid"]
        if row["has_left_arrow"]:
            cls.append("arrow-left")
        if row["has_right_arrow"]:
            cls.append("arrow-right")

        # Mark short events for additional styling
        if duration_days < 0.5:
            cls.append("short-span")

        event_blocks.append(
            html.Button(
                text,
                id={"type": "grid-event", "index": row.get("orig_index", idx)},
                n_clicks=0,
                className=" ".join(cls),
                style={
                    "--row": row_num,
                    "--left": f"{left_pct:.2f}%",
                    "--width": f"{width_pct:.2f}%",
                    "--bg": colors[row["Casino"]]["bg"],
                    "--fg": colors[row["Casino"]]["text"],
                },
                title=f"{row['EventName']} ({row['Casino']})",
                **{
                    "data-eventname": row["EventName"],
                    "data-casino": row["Casino"],
        children=[header_row] + event_blocks + grid_fillers,
                    "data-start": row["StartDate"].strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),  # noqa: E501
                    "data-end": row["EndDate"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "data-offer": row["Offer"],
                },
            )
        )

    grid_fillers = [
        html.Div(
            className="grid-filler-cell",
            style={"gridRow": str(row + 2), "gridColumn": f"{col}"},
        )
        for row in range(event_rows)
        for col in range(1, 8)
    ]

    # 4. Render a single grid container: header labels + event blocks
    return html.Div(
        children=day_labels + event_blocks + grid_fillers,
        className="week-grid",
        style={"gridTemplateRows": "var(--header-row-height) auto"},
    )
