from datetime import datetime
from typing import Any, cast

import pandas as pd
from dash import html

from utils.colors import get_color
from utils.data_parsing import prepare_week_events

from .utils import get_week_range, trim_label


def _normalize(dt):
    """Return ``dt`` converted to a naive UTC datetime."""

    ts = pd.Timestamp(dt)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC")
    return ts.tz_localize(None)


def _build_block(row, week_start, week_end, screen_width, colors):
    """Return button text, classes and style variables for a calendar block."""

    start_delta = (
        _normalize(row["StartDate"]) - _normalize(week_start)
    ).total_seconds() / (24 * 3600)
    end_delta = (
        _normalize(row["EndDate"]) - _normalize(week_start)
    ).total_seconds() / (24 * 3600)

    visible_start = max(start_delta, 0)
    visible_end = min(end_delta, 7)
    span_days = max(visible_end - visible_start, 0)
    row_num = row.get("row_num", 0) + 2

    left_pct = (visible_start / 7) * 100
    width_pct = (span_days / 7) * 100
    if left_pct + width_pct > 100:
        width_pct = 100 - left_pct
    width_pct = max(width_pct, 0)

    font_px = (
        12
        if screen_width < 480
        else 14 if screen_width < 768 else 16 if screen_width < 1024 else 18
    )
    approx_char_px = font_px * 0.6
    block_px = screen_width * (span_days / 7) * 0.95
    max_chars = max(int(block_px / approx_char_px), 0)
    text = trim_label(row["EventName"], max_chars, row.get("OfferType", ""))

    classes = ["event-block-grid"]
    if row["has_left_arrow"]:
        classes.append("arrow-left")
    if row["has_right_arrow"]:
        classes.append("arrow-right")
    if span_days < 0.5:
        classes.append("short-span")

    arrow_left = "calc(-1 * var(--arrow-width))" if row["has_left_arrow"] else "0"
    arrow_right = "calc(-1 * var(--arrow-width))" if row["has_right_arrow"] else "0"

    style = {
        "--row": row_num,
        "--left": f"{left_pct:.2f}%",
        "--width": f"{width_pct:.2f}%",
        "--bg": colors[row["Casino"]]["bg"],
        "--fg": colors[row["Casino"]]["text"],
        "--arrow-left-offset": arrow_left,
        "--arrow-right-offset": arrow_right,
    }

    return text, " ".join(classes), style


def render_week_grid(
    clicked_date: datetime,
    df: pd.DataFrame,
    screen_width: int = 1024,
    selected_casinos: list[str] | None = None,
) -> html.Div:
    """Render a week's events in a CSS grid layout."""

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

    # Filter and annotate events for the week
    filtered = df[df["Casino"].isin(selected_casinos)] if selected_casinos else df
    df_assigned = prepare_week_events(filtered, week_start)

    colors = get_color()

    if df_assigned.empty:
        event_rows = 5
    else:
        max_row = df_assigned["row_num"].max()
        event_rows = int(max_row) + 1

    # Build CSS-grid event-block divs that are clickable
    event_blocks = []
    for idx, row in df_assigned.iterrows():
        text, cls, style = _build_block(row, week_start, week_end, screen_width, colors)

        button_id = {"type": "grid-event", "index": row.get("orig_index", idx)}
        if row.get("is_duplicate"):
            # Add a unique ``dup_idx`` flag so React keys remain unique while the
            # original ``index`` links the duplicate to its modal details.
            button_id.update({"dup": "sunday", "dup_idx": idx})

        event_blocks.append(
            html.Button(
                html.Span(text, className="event-block-grid__text"),
                id=button_id,
                n_clicks=0,
                className=cls,
                style=style,
                title=f"{row['EventName']} ({row['Casino']})",
                **cast(
                    dict[str, Any],
                    {
                        "data-eventname": row["EventName"],
                        "data-casino": row["Casino"],
                        "data-start": row["StartDate"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "data-end": row["EndDate"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "data-offer": row["Offer"],
                    },
                ),
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

    day_clickers = [
        html.Button(
            id={"type": "day-column", "index": date.strftime("%Y-%m-%d")},
            n_clicks=0,
            className="day-click-area",
            title=f"{date.strftime('%b %d')} Events",
            style={"gridColumn": f"{i + 1}", "gridRow": f"2 / {event_rows + 2}"},
            **cast(dict[str, Any], {"data-date": date.strftime("%b %d")}),
        )
        for i, date in enumerate(dates)
    ]

    # 4. Render a single grid container: header labels + event blocks
    return html.Div(
        children=[header_row] + event_blocks + day_clickers + grid_fillers,
        className="week-grid",
    )
