import dash
from dash import html, dcc, Input, Output, State, MATCH, ALL, ctx
import plotly.graph_objs as go
import pandas as pd
from pytz import timezone
from datetime import datetime, timedelta
from math import floor
from typing import Tuple, Dict
import numpy as np
from collections import defaultdict

PDT = timezone('America/Los_Angeles')

# Load CSV file and localize timestamps
df = pd.read_csv("casino_events.csv")
df["StartDate"] = pd.to_datetime(df["StartDate"]).dt.tz_localize(PDT)
df["EndDate"] = pd.to_datetime(df["EndDate"]).dt.tz_localize(PDT)

today = datetime.now(PDT).replace(hour=0, minute=0, second=0, microsecond=0)

# Define default screen width and function to get font sizes
screen_width = 1024 # fallback if not set dynamically

def get_dynamic_sizes(screen_width):
    if screen_width < 480:
        font_sizes = {
            "h1": "1.5rem",
            "legend_title": "1.3rem",
            "legend": "1rem",
            "button": "2.5rem",
            "event_block": "0.8rem",
            "overflow": "0.9rem",
        }
        padding_sizes = {
            "header_padding": "8px 10px",
            "button_padding": "4px 6px",
            "week_gap": "10px",
            "legend_gap": "2px",
            "section_margin": "10px",
        }
    elif screen_width < 768:
        font_sizes = {
            "h1": "2rem",
            "legend_title": "1.5rem",
            "legend": "1.2rem",
            "button": "2.6rem",
            "event_block": "0.9rem",
            "overflow": "1rem",
        }
        padding_sizes = {
            "header_padding": "10px 15px",
            "button_padding": "4px 6px",
            "week_gap": "15px",
            "legend_gap": "8px",
            "section_margin": "15px",
        }
    else:
        font_sizes = {
            "h1": "2.5rem",
            "legend_title": "1.9rem",
            "legend": "1.5rem",
            "button": "2.7rem",
            "event_block": "1rem",
            "overflow": "1.2rem",
        }
        padding_sizes = {
            "header_padding": "15px 20px",
            "button_padding": "4px 6px",
            "week_gap": "20px",
            "legend_gap": "10px",
            "section_margin": "20px",
        }
    return font_sizes, padding_sizes

def get_week_range(clicked_date: datetime) -> Tuple[datetime, datetime]:
    # Determine the week range (Sunday to Saturday)
    week_start = clicked_date - timedelta(days=(clicked_date.weekday() + 1) % 7)
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    return week_start, week_end

def filter_long_spanning_events(events_df: pd.DataFrame, week_start: datetime, week_end: datetime) -> pd.DataFrame:
    # Seperate long-spanning events that cover the entire week
    return events_df[
        (events_df["StartDate"] < week_start) &
        (events_df["EndDate"] > week_end)
    ].copy()
    
def filter_week_events(events_df: pd.DataFrame, week_start: datetime, week_end: datetime) -> pd.DataFrame:
    # Filter events that overlap with the current week, excluding long_spanning events
    return events_df[
        (events_df["EndDate"] > week_start) &
        (events_df["StartDate"] < week_end) &
        ~(events_df["StartDate"] == week_end) &
        ~(
            (events_df["StartDate"] < week_start) &
            (events_df["EndDate"] > week_end)
        )
    ].copy()   
    
def annotate_events_with_flags(events_df: pd.DataFrame, week_start: datetime, week_end: datetime) -> pd.DataFrame:
    # Add a duration column for sorting, and sort by: both left and right arrows, only left arrow, fully within week, and only right arrow
    events_df["Duration"] = (events_df["EndDate"] - events_df["StartDate"]).dt.total_seconds()
    events_df["has_left_arrow"] = events_df["StartDate"] < week_start
    events_df["has_right_arrow"] = events_df["EndDate"] > week_end
    
    def get_overflow_priority(row):
    #Overflow priority: both arrows -> 0, right only -> 1, none -> 2, left only -> 3
        if row["has_left_arrow"] and row["has_right_arrow"]:
            return 1
        if row["has_right_arrow"]:
            return 0
        if not row["has_left_arrow"] and not row["has_right_arrow"]:
            return 2
        return 3
    
    events_df["overflow_sort"] = events_df.apply(get_overflow_priority, axis=1)
    
    return events_df.sort_values(
        by=["overflow_sort", "StartDate", "EndDate", "Duration", "Casino"],
        ascending=[True, True, True, False, True]
    ).reset_index(drop=True)

def assign_event_rows(events_df: pd.DataFrame, week_start: datetime) -> pd.DataFrame:
    # Layout params
    row_unit_height = 0.575
    used_rows_by_day = {i: set() for i in range(7)}
    recurring_rows = defaultdict(int)
    current_row = 0
    row_nums = []
    
    for priority in sorted(events_df["overflow_sort"].unique()):
        group_df = events_df[events_df['overflow_sort'] == priority].sort_values(
            by=["StartDate", "EndDate", "Duration", "Casino"],
            ascending=[True, True, False, True]
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

            #First try preferred row
            if preferred_row is not None and all(preferred_row not in used_rows_by_day[d] for d in range(start_day, end_day + 1)):
                assigned_row = preferred_row
                row_assigned = True
            else:
                for r in range(current_row, 100):
                    if all(r not in used_rows_by_day[d] for d in range(start_day, end_day + 1)):
                        assigned_row = r
                        recurring_rows[recurring_key] = r
                        row_assigned = True
                        break

            #If not usable, find a new row
            if row_assigned:
                for d in range(start_day, end_day + 1):
                    used_rows_by_day[d].add(assigned_row)
                events_df.at[idx, "row_num"] = assigned_row
                row_nums.append(assigned_row)
            
            current_row = max(row_nums, default=current_row) + 1
    
    return events_df

def build_empty_figure() -> go.Figure:
    return go.Figure(
        layout=go.Layout(
            title="No Events This Week",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
    )

def build_weekly_figure(events_df, font_sizes, screen_width, week_start):
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
        (week_start + timedelta(days=i)).strftime('%a') + '<br>' +
        (week_start + timedelta(days=i)).strftime('%b %d') for i in range(7)
    ]

    for i in range(1, 7):
        shapes.append(dict(
            type="line",
            x0=i, x1=i,
            y0=-0.5,
            y1=100,  # placeholder; replaced later
            line=dict(color="black", width=1),
            layer="below"
        ))

    grouped = events_df.copy()

    casino_colors = get_color()

    for priority in sorted(grouped["overflow_sort"].unique()):
        group_df = grouped[grouped["overflow_sort"] == priority]
        group_df = group_df.sort_values(by=["StartDate", "EndDate", "Duration", "Casino"], ascending=[True, True, False, True])

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

            if preferred_row is not None and all(preferred_row not in used_rows_by_day[d] for d in range(start_day, end_day + 1)):
                assigned_row = preferred_row
                row_assigned = True
            else:
                for r in range(current_row, 100):
                    if all(r not in used_rows_by_day[d] for d in range(start_day, end_day + 1)):
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

            # Font and trimming
            CHARS_PER_UNIT = 10 if screen_width < 480 else 20 if screen_width < 768 else 30 if screen_width < 1024 else 40
            max_chars = max(int(block_width * CHARS_PER_UNIT), 0)

            label = row["EventName"]
            trimmed_label = (
                label if len(label) <= max_chars else
                (label[:max_chars - 1] + "...") if max_chars >= 4 else
                "" if max_chars < 4 else "..."
            )

            color = casino_colors[row["Casino"]]["bg"]
            text_color = casino_colors[row["Casino"]]["text"]

            shapes.append(dict(
                type="rect",
                x0=adjusted_start,
                x1=adjusted_end,
                y0=y_center - slot_height / 2,
                y1=y_center + slot_height / 2,
                fillcolor=color,
                line=dict(color="black", width=1),
                layer="above"
            ))

            if row["has_left_arrow"]:
                shapes.append(dict(
                    type="path",
                    path=f"M 0,{y_center} L{ARROW_OFFSET},{y_center + 0.2} L{ARROW_OFFSET},{y_center - 0.2} Z",
                    fillcolor="black",
                    line=dict(color="black", width=1),
                    layer="above"
                ))

            if row["has_right_arrow"]:
                shapes.append(dict(
                    type="path",
                    path=f"M 7,{y_center} L{7 - ARROW_OFFSET},{y_center + 0.2} L{7 - ARROW_OFFSET},{y_center - 0.2} Z",
                    fillcolor="black",
                    line=dict(color="black", width=1),
                    layer="above"
                ))

            try:
                font_size = float(font_sizes["event_block"].replace("rem", "")) * 14
            except:
                font_size = 12

            annotations.append(dict(
                x=(adjusted_start + adjusted_end) / 2,
                y=y_center,
                text=trimmed_label,
                showarrow=False,
                font=dict(size=font_size, color=text_color),
                xanchor="center",
                yanchor="middle"
            ))

            hover_markers.append(go.Scatter(
                x=[(adjusted_start + adjusted_end) / 2],
                y=[y_center],
                text=[label],
                mode="markers",
                marker=dict(size=0, color="rgba(0,0,0,0)"),
                hoverinfo="text",
                showlegend=False,
                customdata=[[row.to_dict()]]
            ))

        current_row = max(row_nums, default=current_row) + 1

    total_rows = max(row_nums, default=0)
    adjusted_rows = max(MIN_ROWS, total_rows)
    base_y_top = adjusted_rows * row_unit_height + 0.5
    chart_height = int(base_y_top * 40)

    # Update lines to correct Y range
    for shape in shapes:
        if shape["type"] == "line":
            shape["y1"] = base_y_top

    return go.Figure(
        data=hover_markers,
        layout=go.Layout(
            shapes=shapes,
            annotations=annotations,
            xaxis=dict(
                type="linear",
                tickmode="array",
                tickvals=[i + 0.5 for i in range(7)],
                ticktext=[f"<b style='color:#00008B;font-size:{font_sizes['event_block']};'>{label}</b>" for label in tick_labels],
                side="top",
                showgrid=True,
                gridcolor="lightgray",
                zeroline=False,
                range=[0, 7],
                fixedrange=True
            ),
            yaxis=dict(
                range=[-0.5, base_y_top + 0.5],
                showgrid=False,
                visible=False,
                fixedrange=True
            ),
            height=chart_height,
            margin=dict(t=40, b=20, l=20, r=20)
        )
    )

 
# Function to generate a weekly view given a clicked date
def generate_weekly_view(clicked_date, screen_width=1024):
    font_sizes, _ = get_dynamic_sizes(screen_width)
    week_start, week_end = get_week_range(clicked_date)

    long_spanning = filter_long_spanning_events(df, week_start, week_end)
    events_filtered = filter_week_events(df, week_start, week_end)

    if events_filtered.empty:
        return build_empty_figure(), long_spanning

    events_annotated = annotate_events_with_flags(events_filtered, week_start, week_end)
    fig = build_weekly_figure(events_annotated, font_sizes, screen_width, week_start)

    return fig, long_spanning


def get_color():
    # Color map by Casino (can expand if needed)
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
        "Seven Feathers Casino": {"bg": "#41c5de", "text": "#000000"}
    }

    default_colors = {
        "#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff",
        "#00ffff", "#ff8000", "#800000", "#008000", "#000080",
        "#800080", "#ffa500", "#808080", "#ff6347", "#ff4500",
        "#ff00ff", "#008080", "#4b0082", "#008b8b", "#000080",
        "#4682b4"
    }

    result = {}
    for casino, colors in color_map.items():
        result[casino] = colors

    if not result:
        print(f"No color assigned for casino: {casino}; using default color.")
        dummy_casinos = [f"Casino {i}" for i in range(len(default_colors))]
        for casino_name, color in zip(dummy_casinos, default_colors):
            result[casino_name] = {"bg": color, "text": "#000000"}

    return result

def create_legend(font_sizes, padding_sizes):
    legend_items = []
    for casino, color in get_color().items():
        if casino in df['Casino'].unique():
            legend_items.append(html.Div([
                html.Div(
                    style={
                        'backgroundColor': color["bg"],
                        'width': '20px',
                        'height': '20px',
                        'display': 'inline-block',
                        'marginRight': '6px'
                    }
                ),
                html.Span(
                    f"{casino}",
                    style={
                        'color': color["bg"],
                        'marginRight': '4px',
                        'fontSize': font_sizes['legend']
                    }
                )
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'margin': f"0 {padding_sizes['legend_gap']} {padding_sizes['legend_gap']} 0",
                'flex': '0 1 auto',
            }))
    return legend_items

today = datetime.now(PDT)
current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
week_offset = 0
start_sunday = current_sunday + timedelta(weeks=week_offset)
rolling_weeks = [start_sunday + timedelta(weeks=i) for i in range(4)]

#Determine responsive font sizes based on screen width
font_sizes, padding_sizes = get_dynamic_sizes(screen_width)
font_size_small = font_sizes['button']
font_size_medium = font_sizes['legend']
font_size_large = font_sizes['h1']

# Build the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

app.title = "Casino Event Calendar"

#Client-sde callback to get screen-width
app.clientside_callback(
    '''
    function(n_intervals) {
        return window.innerWidth;
    }
    ''',
    Output('screen-width', 'data'),
    Input('initial-trigger', 'n_intervals'), 
    State('screen-width', 'data')
)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = html.Div(
    style={
        'fontFamily': 'Segoe UI, sans-serif',
        'margin': '0 auto',
        'paddingBottom': '40px'
    },
    children=[
        #Sticky-Header container
        html.Div(id='sticky-header', style={
            'position': 'sticky',
            'top': 0,
            'padding': f"{padding_sizes['header_padding']} 0",
            'backgroundColor': 'white',
            'zIndex': 1000,
            'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.25)'
        }),
        
        #Loading spinner and calendar weeks
        dcc.Loading(
            id='calendar-loading',
            type='circle',
            color='#6A5ACD',
            children=html.Div(
                id='rolling-weeks',
                style={
                    'display': 'flex',
                    'flexDirection': 'column',
                    'gap': padding_sizes['week_gap'],
                    'marginTop': padding_sizes['section_margin']
            }),
        ),
        
        #State Stores and Timers
        dcc.Store(id='screen-width', data=1024), 
        dcc.Store(id='week-offset', data=0),
        dcc.Interval(id='initial-trigger', interval=1, max_intervals=1),
        dcc.Interval(id='close-timer', interval=600, n_intervals=0, max_intervals=0),
     
        #Modal Popup for event details
        html.Div(id='event-modal', className='modal', children=[
            html.Div(id='event-modal-content', className='modal-content', children=[
                html.Div(id='event-modal-body'),
                html.Button("Close", id="close-modal", style={
                    'marginTop': '10px',
                    'display': 'block',
                    'marginLeft': 'auto',
                    'marginRight': 'auto',
                    'backgroundColor': '#6A5ACD',
                    'color': 'white',
                    'border': 'none',
                    'padding': '8px 16px',
                    'borderRadius': '6px',
                    'cursor': 'pointer'
                })
            ])
        ])
    ]
    )

@app.callback(
    # print(f"Triggered by: {ctx.triggered}"),
    Output('sticky-header', 'children'),
    Input('screen-width', 'data')
)

def sticky_header(screen_width):
    font_sizes, padding_sizes = get_dynamic_sizes(screen_width)

    return html.Div([
        html.H1(
            "🎰 Casino Event Calendar 📅",
            style={
                'textAlign': 'center',
                'margin': '0',
                'fontSize': font_sizes['h1'],
                'marginBottom': '20px',
                'color': 'inherit',
                'padding': f"{padding_sizes['header_padding']} 0",
            }
        ),
        #Navigation & Legend
        html.Div(
            id='header-container',
            children=[
            html.Button(
                "🎲",
                id='prev-button',
                title="Prior 4 Weeks",
                n_clicks=0,
                className='emoji-button',
                style={'fontSize': font_sizes['button'], 'padding': padding_sizes['button_padding']}
            ),
            html.Div([
                html.Legend(
                    "Casino Legend:",
                    style={
                        'fontWeight': 'bold',
                        'textAlign': 'center',
                        'fontSize': font_sizes['legend_title'],
                        'marginBottom': padding_sizes['legend_gap']
                    }
                ),
                html.Div(
                    create_legend(font_sizes, padding_sizes),
                    style={
                        'display': 'flex',
                        'flexWrap': 'wrap',
                        'justifyContent': 'center',
                        'alignItems': 'flex-start',
                        'textAlign': 'left',
                        'gap': f"{int(padding_sizes['legend_gap'].replace('px', '')) // 2}px"
                    }
                )
            ], style={'flex': '1', }),
            html.Button(
                "🎰",
                id='next-button',
                title="Upcoming 4 Weeks",
                n_clicks=0,
                className='emoji-button',
                style={'fontSize': font_sizes['button'], 'padding': padding_sizes['button_padding']}
            )
        ],
        style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'gap': '10px',
            'paddingBottom': '10px',
        }
        )
    ])

@app.callback(
    Output('week-offset', 'data'),
    Output('prev-button', 'disabled'),
    Output('next-button', 'disabled'),
    Input('prev-button', 'n_clicks'),
    Input('next-button', 'n_clicks'),
    State('week-offset', 'data')
)

def update_week_offset(prev_clicks, next_clicks, current_offset):
    desired_offset = next_clicks - prev_clicks
    
    #Limit going back no more than 6 weeks
    if desired_offset < -6:
        desired_offset = -6
        
    #Limit forward navigation if next 4 weeks are empty
    today = datetime.now(PDT)
    current_sunday = today - timedelta(days=(today.weekday() + 1 ) % 7)
    start_sunday = current_sunday + timedelta(weeks=desired_offset)
    rolling_weeks = [start_sunday + timedelta(weeks=i) for i in range(4)]
    
    #Check if there are events in next 4 weeks
    has_future_events = any(
        not df[(df['EndDate'] > week) & (df['StartDate'] < week + timedelta(days=6))].empty
        for week in rolling_weeks
    )
    
    #Don't allow forward if not future events
    if not has_future_events and desired_offset > current_offset:
        desired_offset = current_offset
        
    #Disable determination if no events moving forward
    prev_disabled = desired_offset <= -6
    next_disabled = not has_future_events
    
    return desired_offset, prev_disabled, next_disabled

@app.callback(
    Output('rolling-weeks', 'children'),
    Input('week-offset', 'data'),
    Input('initial-trigger', 'n_intervals'),
    State('screen-width', 'data'),
    prevent_initial_call=True
)

def render_weeks(week_offset, _, screen_width):
    if week_offset is None or not isinstance(week_offset, int):
        week_offset = 0

    # Recalculate weeks and figures based on the current week offset
    today = datetime.now(PDT)
    current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    start_sunday = current_sunday + timedelta(weeks=week_offset)
    rolling_weeks = [start_sunday + timedelta(weeks=i) for i in range(4)]

    font_sizes, padding_sizes = get_dynamic_sizes(screen_width)
    weekly_blocks = []

    for i, start_date in enumerate(rolling_weeks):
        fig, overflow_df = generate_weekly_view(start_date, screen_width)
        
        week_key = f"week-{start_date.strftime('%Y%m%d')}"
        end_date = start_date + timedelta(days=6)
        
        toggle_id = {'type': 'toggle-week', 'index': i}
        content_id = {'type': 'week-content', 'index': i}
        
        overflow_width = '80%' if screen_width < 480 else '60%' if screen_width < 768 else '40%'
        
        overflow_content = html.Div(
            id={'type': 'overflow-box', 'index': i},
            className='overflow-box',
            children=[
                html.Strong("Ongoing Events This Week:", style={
                    'color': '#6A5ACD',
                    'textWeight': 'bold', 
                    'fontSize': font_sizes['overflow'], 
                    'display': 'block', 
                    'marginBottom': '8px'
                }),
                html.Ul([
                    html.Li(
                        f"{row['EventName']} ({row['Casino']}) - {row['StartDate'].strftime('%b %d')} to {row['EndDate'].strftime('%b %d')}", 
                        style={'color': '#00008B', 'fontSize': font_sizes['overflow']}
                    )
                    for _, row in overflow_df.iterrows()
                ])
            ],
            style={
                'backgroundColor': '#f5f3fa',  # Overflow-box background
                'padding': '12px 20px',
                'border': '2px solid #ccc',
                'borderRadius': '4px',
                'margin': '0 auto 10px auto',
                'width': overflow_width,
                'textAlign': 'left',
            }
        )
        
        weekly_blocks_children = [
            dcc.Store(id={'type': 'week-toggle', 'index': i}, data=False),
            dcc.Store(id={'type': 'toggle-date', 'index': i}, data=start_date.strftime('%Y-%m-%d')),
            dcc.Store(id={'type': 'overflow-date', 'index': i}, data=start_date.strftime('%Y-%m-%d')),
            html.H3(
                f"▶ Events the Week of {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}",
                id=toggle_id,
                className='week-header',
                n_clicks=0,
                style={
                    'fontSize': font_sizes['legend_title'],
                    'color': '#6A5ACD',
                    'fontWeight': 'bold',
                    'cursor': 'pointer',
                    'textAlign': 'center',
                    'userSelect': 'none',
                    'margin': 0
                }
            ),
            html.Div(
                id=content_id,
                className='week-content',
                children=[
                    dcc.Graph(
                        id={'type': 'graph', 'index': i},
                        figure=fig,
                        config={'displayModeBar': False},
                        style={'width': '99%'}
                    ),
                    html.Div([
                        # Collapse Toggle
                        html.Button(
                            f"🌀 Show Ongoing Events for {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}",
                            id={'type': 'overflow-toggle', 'index': i},
                            n_clicks=0,
                            style={
                                'color': '#00008B',
                                'fontSize': font_sizes['overflow'],
                                'padding': '2px 4px',
                                'textAlign': 'center',
                                'display': 'flex',
                                'alignItems': 'center',
                                'justifyContent': 'center'
                            }
                        ),
                        overflow_content
                    ]) if not overflow_df.empty else html.Div()
                ]
            )
        ]
            
        weekly_blocks.append(
            html.Div(
                weekly_blocks_children,
                style={'marginBottom': padding_sizes['section_margin']}
                )
            )      
    
    # Return a list of figures for the weeks
    return weekly_blocks

@app.callback(
    Output({'type': 'week-content', 'index': MATCH}, 'className'),
    Output({'type': 'week-toggle', 'index': MATCH}, 'data'),
    Input({'type': 'toggle-week', 'index': MATCH}, 'n_clicks'),
    State({'type': 'week-toggle', 'index': MATCH}, 'data'),
    prevent_initial_call=True
)

def toggle_week_content(n_clicks, is_open):
    new_is_open = not is_open
    new_class = 'week-content show' if new_is_open else 'week-content'
    return new_class, new_is_open

@app.callback(
    Output({'type': 'toggle-week', 'index': MATCH}, 'children'),
    Input({'type': 'week-toggle', 'index': MATCH}, 'data'),
    State({'type': 'toggle-date', 'index': MATCH}, 'data')
)

def update_toggle_title(is_open, start_date_str):
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = start_date + timedelta(days=6)
    return (
        f"▼ Events the Week of {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
        if is_open else
        f"▶ Events the Week of {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
    )

@app.callback(
    Output({'type': 'overflow-box', 'index': MATCH}, 'className'),
    Output({'type': 'overflow-toggle', 'index': MATCH}, 'children'),
    Input({'type': 'overflow-toggle', 'index': MATCH}, 'n_clicks'),
    State({'type': 'overflow-date', 'index': MATCH}, 'data'),
    prevent_initial_call=True
)

def toggle_overflow(n_clicks, start_date_str):
    # print(f"[toggle_overflow] Clicks: {n_clicks}, Date: {start_date_str}")
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = start_date + timedelta(days=6)
    is_open = n_clicks % 2 == 1

    box_class = 'overflow-box show' if is_open else 'overflow-box'

    button_text = (
        f"🌀 Hide Ongoing Events for {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
        if is_open else 
        f"🌀 Show Ongoing Events for {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
    )

    return box_class, button_text

@app.callback(
    Output('event-modal', 'style'),
    Output('event-modal', 'className'),
    Output('event-modal-body', 'children'),
    Output('close-timer', 'n_intervals'),
    Output({'type': 'graph', 'index': ALL}, 'clickData'),
    Input({'type': 'graph', 'index': ALL}, 'clickData'),
    Input("close-modal", "n_clicks"),
    Input("close-timer", "n_intervals"),
    prevent_initial_call=True
)

def show_event_modal(clicks, close_clicks, timer_tick):
    ctx = dash.callback_context

    #Make sure clicks is a list
    if not clicks or not isinstance(clicks, list):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, []

    #Reser modal on timer triggered
    if ctx.triggered_id == "close-timer":
        return dash.no_update, '', "", 0, [None] * len(clicks)
    
    #Handle close button click
    if ctx.triggered_id == "close-modal":
        return dash.no_update, 'modal closing', dash.no_update, 1, [None] * len(clicks)
    
    #Check for valid clickData    
    for click in clicks:
        if click and isinstance(click, dict) and 'points' in click and click['points']:
            data = click['points'][0].get('customdata', [None])[0]
            if not data:
                continue
            
            rows = []
            for label in ["EventName", "Casino", "Location", "StartDate", "EndDate", "Offer"]:
                if label in data:
                    display_label = {
                        "EventName": "Event",
                        "StartDate": "Event Starts",
                        "EndDate": "Event Ends"
                    }.get(label, label)

                    value = data[label]

                    if label in ["StartDate", "EndDate"]:
                        try:
                            value = pd.to_datetime(value).strftime("%b %d, %Y @ %I:%M %p")
                        except Exception:
                            pass

                    rows.append(html.Div([
                        html.Strong(f"{display_label}: ", style={'color': '#6A5ACD'}),
                        html.Span(value)
                    ], style={'marginBottom': '6px'}))
            return {}, 'modal show', rows, 0, [None] * len(clicks)
    #If nothing is valid was clicked
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, [None] * len(clicks)

server = app.server
# Run the Dash app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=True)