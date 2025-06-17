from math import floor

import pandas as pd
from dash import html

from .plotting import (annotate_events_with_flags, assign_event_rows,
                       filter_week_events, get_color)
from .utils import get_week_range


def render_week_grid(clicked_date, df):
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

        start_index = max(0, int(floor(visible_start)))
        end_index = min(6, int(floor(visible_end - 1e-6)))

        col_start = start_index + 1
        col_end = end_index + 2

        row_num = row["row_num"] + 2

        # Trim label if too long
        label = row["EventName"]
        max_chars = int((col_end - col_start) * 30)
        text = (
            label
            if len(label) < max_chars
            else label[: max_chars - 2] + "..." if max_chars >= 3 else "..."
        )

        # Determine arrow classes
        cls = ["event-block-grid"]
        if row["has_left_arrow"]:
            cls.append("arrow-left")
        if row["has_right_arrow"]:
            cls.append("arrow-right")

        event_blocks.append(
            html.Button(
                text,
                id={"type": "grid-event", "index": row.get("orig_index", idx)},
                n_clicks=0,
                className=" ".join(cls),
                style={
                    "--row": row_num,
                    "--col-start": col_start,
                    "--col-end": col_end,
                    "--bg": colors[row["Casino"]]["bg"],
                    "--fg": colors[row["Casino"]]["text"],
                },
                title=f"{row['EventName']} ({row['Casino']})",
                **{
                    "data-eventname": row["EventName"],
                    "data-casino": row["Casino"],
                    "data-location": row["Location"],
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
