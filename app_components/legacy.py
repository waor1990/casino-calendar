from datetime import timedelta
from math import floor

import plotly.graph_objs as go

from .plotting import annotate_events_with_flags, filter_week_events, get_color
from .utils import get_week_range, trim_label

"""Legacy Plotly rendering code preserved for reference."""


def filter_long_spanning_events(events_df, week_start, week_end):
    """Return events that span the entire week."""
    return events_df[
        (events_df["StartDate"] < week_start) & (events_df["EndDate"] > week_end)
    ].copy()


def build_empty_figure():
    """Return an empty placeholder Plotly figure."""
    return go.Figure(
        layout=go.Layout(
            title="No Events This Week",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
    )


def build_weekly_figure(events_df, screen_width, week_start):
    """Create the weekly Plotly figure used before the CSS grid version."""
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


def generate_weekly_view(clicked_date, df, screen_width=1024):
    """Return the legacy Plotly weekly view and long-spanning events."""
    week_start, week_end = get_week_range(clicked_date)

    long_spanning = filter_long_spanning_events(df, week_start, week_end)
    events_filtered = filter_week_events(df, week_start, week_end)

    if events_filtered.empty:
        return build_empty_figure(), long_spanning

    events_annotated = annotate_events_with_flags(events_filtered, week_start, week_end)
    fig = build_weekly_figure(events_annotated, screen_width, week_start)

    return fig, long_spanning
