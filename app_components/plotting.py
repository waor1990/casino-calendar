import plotly.graph_objs as go
import pandas as pd
from dash import html, dcc
from datetime import datetime, timedelta
from math import floor
from collections import defaultdict
from .utils import get_dynamic_sizes, get_week_range, PDT

#Layout config shared across functions
def get_layout_config(screen_width):
    font_sizes, padding_sizes = get_dynamic_sizes(screen_width)
    hour_height = 40 if screen_width < 480 else 50
    label_column_pct = 10
    return font_sizes, padding_sizes, hour_height, label_column_pct

# Function to generate a weekly view given a clicked date
def generate_weekly_view(clicked_date, df, screen_width=1024):
    font_sizes, _ = get_dynamic_sizes(screen_width)
    week_start, week_end = get_week_range(clicked_date)

    long_spanning = filter_long_spanning_events(df, week_start, week_end)
    events_filtered = filter_week_events(df, week_start, week_end)

    if events_filtered.empty:
        return build_empty_figure(), long_spanning

    events_annotated = annotate_events_with_flags(events_filtered, week_start, week_end)
    fig = build_weekly_figure(events_annotated, font_sizes, screen_width, week_start)

    return fig, long_spanning

#Color map by Casino
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
        "Tulalip Casino": {"bg": "#155e6d", "text":"#ffffff"},
        "Quil Ceda Creek Casino": {"bg": "#9a0709", "text": "#ffffff"},
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

#Add arrow indicators for events that span outside the week
def annotate_events_with_flags(events_df: pd.DataFrame, week_start: datetime, week_end: datetime) -> pd.DataFrame:
    # Add a duration column for sorting, and sort by: both left and right arrows, only left arrow, fully within week, and only right arrow
    events_df["Duration"] = (events_df["EndDate"] - events_df["StartDate"]).dt.total_seconds()
    events_df["has_left_arrow"] = events_df["StartDate"] < week_start
    events_df["has_right_arrow"] = events_df["EndDate"] > week_end
    
    def get_overflow_priority(row):
    #Overflow priority: both arrows -> 0, right only -> 1, none -> 2, left only -> 3
        if row["has_left_arrow"] and row["has_right_arrow"]:
            return 0
        if row["has_right_arrow"]:
            return 1
        if not row["has_left_arrow"] and not row["has_right_arrow"]:
            return 3
        return 2
    
    events_df["overflow_sort"] = events_df.apply(get_overflow_priority, axis=1)
    
    return events_df.sort_values(
        by=["overflow_sort", "StartDate", "EndDate", "Duration", "Casino"],
        ascending=[True, True, True, False, True]
    ).reset_index(drop=True)

# Seperate long-spanning events that cover the entire week
def filter_long_spanning_events(events_df, week_start, week_end):
    return events_df[
        (events_df["StartDate"] < week_start) &
        (events_df["EndDate"] > week_end)
    ].copy()

# Filter events that overlap with the current week, excluding long_spanning events
def filter_week_events(events_df, week_start, week_end):
    return events_df[
        (events_df["EndDate"] > week_start) &
        (events_df["StartDate"] < week_end) &
        ~(events_df["StartDate"] == week_end) &
        ~((events_df["StartDate"] < week_start) & (events_df["EndDate"] > week_end))
    ].copy()

def assign_event_rows(events_df, week_start):
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

def build_empty_figure():
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
                (label[:max_chars - 2] + "...") if max_chars >= 3 else
                "" if max_chars < 3 else "..."
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
                font_size = float(font_sizes["event_block"].replace("rem", "")) * 12
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
                marker=dict(size=30, opacity=0.2, color="orange"),
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
            
    for day_index in range(7):
        hover_markers.append(go.Scatter(
            x=[day_index + 0.5],
            y=[base_y_top + 0.5],
            mode="markers",
            marker=dict(size=20, opacity=0.2, color='red'),
            hoverinfo="text",
            hovertext=["View Day's Events"],
            customdata=[[{
                "type": "day_click",
                "day_index": day_index
            }]],
            showlegend=False,
            name="",
        ))
    

    return go.Figure(
        data=hover_markers,
        layout=go.Layout(
            clickmode='event+select',
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

#Generate a responsive 24-hour vertical day view with absolutely positioned event blocks.
def generate_day_view_html(events_df, clicked_date, get_color_fn, screen_width=1024):
    font_sizes, padding_sizes, hour_height, label_column_pct = get_layout_config(screen_width)

    #Normalize clicked_date
    day_start = clicked_date.astimezone(PDT).replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    
    #Filter events strictly within the day
    events = events_df.copy()
    events["StartDate"] = pd.to_datetime(events["StartDate"]).dt.tz_convert(PDT)
    events["EndDate"] = pd.to_datetime(events["EndDate"]).dt.tz_convert(PDT)
    events = events[
        (events["StartDate"] >= day_start) & 
        (events["EndDate"] <= day_end)
    ]
    
    day_label = clicked_date.strftime("%A, %B %d")
    
    if events.empty:
        return [html.Div(f"No events scheduled for {day_label}.", style={
            "textAlign": "center",
            "padding": padding_sizes.get("base", "1rem"),
            "fontSize": font_sizes.get("legend_title", "1.1rem")
        })]

    #Time math
    events["start_offset_min"] = (events["StartDate"] - day_start).dt.total_seconds() / 60
    events["end_offset_min"] = (events["EndDate"] - day_start).dt.total_seconds() / 60
    events["duration_min"] = events["end_offset_min"] - events["start_offset_min"]
    events = events.sort_values(by=["start_offset_min", "duration_min"])

    #Assign tracks dynamically to avoid overlap
    tracks = []
    track_assignments = []

    for _, event in events.iterrows():
        placed = False
        for i, track in enumerate(tracks):
            if all(event["start_offset_min"] >= t[1] or event["end_offset_min"] <= t[0] for t in track):
                track.append((event["start_offset_min"], event["end_offset_min"]))
                track_assignments.append(i)
                placed = True
                break
        if not placed:
            tracks.append([(event["start_offset_min"], event["end_offset_min"])])
            track_assignments.append(len(tracks) - 1)
        
    events["overlap_index"] = track_assignments
    n_tracks = len(tracks)
    width_pct = (100 - label_column_pct) / n_tracks
    
    color_map = get_color_fn()
    hour_blocks = []
    event_blocks = []
    click_markers = []

    for hour in range(24):
        top_px = hour * hour_height
        label = f"{hour:02d}:00" if hour % 3 == 0 else ""
        
        #Label on left
        hour_blocks.append(html.Div(
            label, 
            style={
                "position": "absolute",
                "top": f"{top_px}px",
                "left": "0",
                "width": f"{label_column_pct}%",
                "height": f"{hour_height}px",
                "fontSize": font_sizes.get('overflow', '0.75rem'),
                "color": "#6A5ACD",
                "paddingLeft": padding_sizes.get("small", "6px"),
                "boxSizing": "border-box",
                "zIndex": 5,
                "backgroundColor": "#f5f3fa"
            }
        ))
        
    # #Full-width grid line
    # hour_blocks.append(html.Div(
    #     "",
    #     style={
    #         "position": "absolute",
    #         "top": f"{top_px}px",
    #         "left": "0",
    #         "width": "100%",
    #         "height": "1px",
    #         "backgroundColor": "#aaa",
    #         "opacity": 0.7,
    #         "zIndex": 1,
    #     }
    # ))  
    
    #Event blocks + invisible click markers
    for _, row in events.iterrows():
        top_px = row["start_offset_min"] / 60 * hour_height 
        height_px = max(20, row["duration_min"] / 60 * hour_height)
        left_pct = label_column_pct + row["overlap_index"] * width_pct

        color = color_map.get(row["Casino"], {"bg": "#aaa"})["bg"]

        #Visible block
        event_blocks.append(html.Div(
            title=row["EventName"],
            style={
                "position": "absolute",
                "top": f"{top_px}px",
                "left": f"{left_pct}%",
                "width": f"{width_pct}%",
                "height": f"{height_px}px",
                "backgroundColor": color,
                "border": "2px solid #444",
                "borderRadius": padding_sizes.get("xxs", "4px"),
                "boxSizing": "border-box",
                "zIndex": 10,
                "cursor": "pointer"
            }
        ))
        
        #Invisible click marker for modal
        center_y = top_px + height_px / 2
        event_data = row[["EventName", "Casino", "Location", "StartDate", "EndDate", "Offer"]].to_dict()
        
        click_markers.append(go.Scatter(
            x=[0.5],
            y=[center_y],
            mode="markers",
            marker=dict(size=40, opacity=0.3, color="orange"),
            customdata=[[event_data]],
            hoverinfo="skip",
            showlegend=False
        ))
    
    #Clickable overlay graph
    click_graph = dcc.Graph(
        id="day-event-catcher",
        figure=go.Figure(
            data=click_markers,
            layout=go.Layout(
                clickmode='event+select',
                xaxis=dict(visible=False, range=[0,1], fixedrange=True),
                yaxis=dict(visible=False, range=[0, 24 * hour_height], fixedrange=True),
                margin=dict(l=0, r=0, t=0, b=0),
                height=24 * hour_height,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
        ),
        config={'displayModeBar': False},
        style={
            "position": "absolute",
            "top": "0",
            "left": "0",
            "width": "100%",
            "height": f"{24 * hour_height}px",
            "zIndex": 1000,
            "pointerEvents": "auto"
        }
    )

    #Sticky Add day label + scrollable grid container
    header = html.Div(
        day_label,
        style={
            "fontWeight": "bold",
            "fontSize": font_sizes.get("legend_title", "1.1rem"),
            "marginBottom": padding_sizes.get("small", "12px"),
            "textAlign": "center",
            "color": "#00008B",
            "position": "sticky",
            "top": "0",
            "zIndex": 15,
            "backgroundColor": "#f5f3fa",
            "padding": padding_sizes.get("xxs", "6px")
        }
    )
    
    return [
        header,
        html.Div(
            children=hour_blocks + event_blocks + [click_graph],
            style={
                "position": "relative",
                "height": f"{24 * hour_height}px",
                "width": "100%",
                "boxSizing": "border-box"
            }
        )
    ]