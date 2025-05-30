from dash import html
import pandas as pd
from datetime import datetime, timedelta
from math import floor
from .utils import get_week_range, PDT
from .plotting import get_color

def render_week_grid(clicked_date, df):
    week_start, week_end = get_week_range(clicked_date)
    df = df.copy()
    
    #Filter events within the week
    df = df[(df['EndDate'] > week_start) & (df['StartDate'] < week_end)]
    
    casino_colors = get_color()
    events_by_day = {i: [] for i in range(7)}
    
    for _, row in df.iterrows():
        start_day = max(0, min(6, (row["StartDate"].date() - week_start.date()).days))
        end_day = min(6, (row["EndDate"].date() - week_start.date()).days)
        duration = end_day - start_day + 1
        
        color = casino_colors[row["Casino"]]["bg"]
        text_color = casino_colors[row["Casino"]]["text"]
        label = f"{row['EventName']} ({row['Casino']})"
        
        block = html.Div(
            label,
            className="event-block-grid",
            style={
                "top": f"{10 + len(events_by_day[start_day]) * 40}px",
                "left": "0",
                "width": f"{duration * 100}%",
                "backgroundColor": color,
                "color": text_color,
            },
            title=label
        )
        
        events_by_day[start_day].append(block)
        
    #Build each day coloumn
    day_columns = []
    for i in range(7):
        date = week_start + timedelta(days=i)
        day_label = date.strftime("%a %b %d")
        
        day_col = html.Div(
            children=[
                html.Strong(day_label, style={"display": "block", "marginBottom": "6px"}),
                *events_by_day[i]
            ],
            className="day-column"
        )
        day_columns.append(day_col)
        
    return html.Div(
        children=day_columns,
        className="week-grid"
    )