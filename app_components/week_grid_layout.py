from dash import html
import pandas as pd
from datetime import datetime, timedelta
from math import floor
from .utils import get_week_range, PDT
from .plotting import (
    filter_long_spanning_events,
    filter_week_events,
    annotate_events_with_flags,
    assign_event_rows,
    get_color
)

def render_week_grid(clicked_date, df):
    #Calculate week bounds
    week_start, week_end = get_week_range(clicked_date)
    dates = pd.date_range(week_start, periods=7)
    #Build 7 day-label divs for header row
    day_labels = []
    for i, date in enumerate(dates):
        day_labels.append(
            html.Div(
                children=[
                    html.Div(date.strftime('%a')),
                    html.Div(date.strftime('%b %d'))
                ],
                className='day-label-grid',
                style={'gridColumn': f'{i + 1}'},
            )
        )

    #Filer/annotate/assign events 
    df_week = filter_week_events(df, week_start, week_end)
    df_annot = annotate_events_with_flags(df_week, week_start, week_end)
    df_assigned = assign_event_rows(df_annot, week_start)
    colors = get_color()  

    if df_assigned.empty:
        event_rows = 5 
    else: 
        max_row = df_assigned['row_num'].max()
        event_rows = int(max_row) + 1

    total_rows = event_rows + 1

    # Build CSS--grid event-block divs that are clickable
    event_blocks = []
    for idx, row in df_assigned.iterrows():
        raw_start_days = (row['StartDate'] - week_start).total_seconds() / (24 * 3600)
        if raw_start_days >= 7 - 1e-6:  # Allow for floating point precision issues
            start_index = 6
        else: 
            start_index = max(0, int(floor(raw_start_days)))
        raw_end_days = (row['EndDate'] - week_start).total_seconds() / (24 * 3600)

        end_index = min(6, int(raw_end_days)) if raw_end_days <= 6 else 6

        col_start = start_index + 1
        col_end = end_index + 2

        row_num = row['row_num'] + 2

        #Trim label if too long
        label = row['EventName']
        max_chars = int((col_end - col_start) * 30)
        text = (label if len(label) < max_chars else 
                 label[:max_chars-2] + '...' if max_chars>=3 else
                 "...")

        #Determine arrow classes
        cls = ["event-block-grid"]
        if row["has_left_arrow"]: cls.append("arrow-left")
        if row["has_right_arrow"]: cls.append("arrow-right")

        event_blocks.append(
            html.Button(
                text,
                id={"type": "grid-event", "index": idx},
                n_clicks=0,
                className=" ".join(cls),
                style={
                    "--row": row_num,
                    "--col-start": col_start,
                    "--col-end": col_end,
                    "--bg": colors[row["Casino"]]["bg"],
                    "--fg": colors[row["Casino"]]["text"]
                },
                title=f"{row['EventName']} ({row['Casino']})",
                **{
                    "data-eventname": row['EventName'],
                    "data-casino": row['Casino'],
                    "data-location": row['Location'],
                    "data-start": row['StartDate'].strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "data-end": row['EndDate'].strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "data-offer": row['Offer'],
                }
            )
        )
        
    grid_fillers = [
        html.Div(
            className="grid-filler-cell",
            style={
                "gridRow": str(row + 2),
                "gridColumn": f"{col}"
            }
        )
        for row in range(event_rows)
        for col in range(1, 8)
    ]
        
    #4. Render a single grid container: header labels + event blocks
    return html.Div(
        children=day_labels + event_blocks + grid_fillers,
        className="week-grid", 
        style={"gridTemplateRows": f"var(--header-row-height) auto"}
    )
    