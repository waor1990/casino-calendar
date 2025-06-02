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
    #Build 7 day-label divs for header row
    day_labels = []
    for date in pd.date_range(week_start, periods=7, freq='D'):
        day_labels.append(
            html.Div(
                date.strftime('%a %b %d'),
                className='day-label-grid'
            )
        )
        
    #Build 7 "column separator" divs for grid layout
    col_separators = []
    col_separators.append(
        html.Div(
            "",
            className="col-separator",
            style={
                'gridColumn': '1',
                'gridRow': '2 / -1',
            }
        )
    )
    for col in range(2, 8):
        col_separators.append(
            html.Div(
                "",
                className="col-separator",
                style={
                    'gridColumn': f"{col}",
                    'gridRow': "2 / -1",
                    'transform': 'translateX(calc(100% - 7.5px))'
                }
            )
        )
    
    col_separators.append(
        html.Div(
            "",
            className="col-separator",
            style={
                'gridColumn': '8',
                'gridRow': '2 / -1',
                'transform': 'translateX(-10px)',
            }
        )
    )
        
    #Filer/annotate/assign events 
    df_week = filter_week_events(df, week_start, week_end)
    df_annot = annotate_events_with_flags(df_week, week_start, week_end)
    df_assigned = assign_event_rows(df_annot, week_start)
    colors = get_color()  
    
    # Build CSS--grid event-block divs that are clikcable
    event_blocks = []
    for idx, row in df_assigned.iterrows():
        #start_delta = max(0, (row['StartDate'] - week_start).days)
        #end_delta = min(7, (row['EndDate'] - week_start).days)
        raw_start_days = (row['StartDate'] - week_start).total_seconds() / (24 * 3600)
        raw_end_days = (row['EndDate'] - week_start).total_seconds() / (24 * 3600)
        
        start_index = max(0, int(raw_start_days))
        if raw_end_days > 6:
            end_index = 6
        else:
            end_index = max(0, int(raw_end_days))
            
        col_start = start_index + 1
        col_end = end_index + 2
        
        row_num = row['row_num'] + 2
        
        #Trim label if too long
        label = row['EventName']
        max_chars = int((col_end - col_start) * 25)
        text = (label if len(label) <- max_chars else 
                 label[:max_chars-2] + '...' if max_chars>=3 else
                 "" if max_chars<1 else "...")
        
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
        
        #4. Render a single grid container: header labels + event blocks
    children = day_labels + col_separators + event_blocks
    return html.Div(children=children, className="week-grid")
    