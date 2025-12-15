"""Helpers for building the weekly grid layout displayed in Dash."""

from datetime import datetime
from typing import Any, cast

import pandas as pd
from casino_calendar.services.colors import get_color, resolve_casino_color
from casino_calendar.services.data_parsing import prepare_week_events
from dash import html

from ..services.layout_state import get_week_range, to_pdt, trim_label


def _normalize(dt):
    """Return ``dt`` converted to a naive UTC datetime."""

    ts = pd.Timestamp(dt)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC")
    return ts.tz_localize(None)


def _build_block(row, week_start, week_end, screen_width, colors):
    """Return button text, classes, style variables, and metadata for a calendar block."""

    start_delta = (
        _normalize(row["StartDate"]) - _normalize(week_start)
    ).total_seconds() / (24 * 3600)
    end_delta = (
        _normalize(row["EndDate"]) - _normalize(week_start)
    ).total_seconds() / (24 * 3600)

    visible_start = max(start_delta, 0)
    visible_end = min(end_delta, 7)
    span_days = max(visible_end - visible_start, 0)
    # Offset rows by one since the grid no longer includes a header row
    row_num = row.get("row_num", 0) + 1

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

    color_entry = resolve_casino_color(row["Casino"], palette=colors)

    style = {
        "--row": row_num,
        "--left": f"{left_pct:.2f}%",
        "--width": f"{width_pct:.2f}%",
        "--bg": color_entry["bg"],
        "--fg": color_entry["text"],
        "--bg-dark": color_entry["bg_dark"],
        "--fg-dark": color_entry["text_dark"],
        "--arrow-left-offset": arrow_left,
        "--arrow-right-offset": arrow_right,
    }

    data_attributes = {
        "data-bg": color_entry["bg"],
        "data-bg-dark": color_entry["bg_dark"],
    }

    return text, " ".join(classes), style, data_attributes


def render_day_labels(week_start: datetime) -> list[html.Div]:
    """Return a list of day label divs for the week starting on Sunday."""

    dates = pd.date_range(week_start, periods=7)

    return [
        html.Div(
            [
                html.Div(to_pdt(date).strftime("%a")),
                html.Div(to_pdt(date).strftime("%b %d")),
            ],
            className="day-label-grid",
            style={"gridColumn": f"{i + 1}"},
        )
        for i, date in enumerate(dates)
    ]


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
    event_blocks: list[Any] = []

    if df_assigned.empty:
        if selected_casinos:
            joined = ", ".join(selected_casinos)
            msg = f"No Events at {joined} have been logged for this week."
        else:
            msg = "No Events have been logged for this week."
        event_blocks.append(
            html.Div(
                msg,
                className="no-events",
                style={"gridRow": "1", "gridColumn": "1 / 8"},
            )
        )
    else:
        for idx, row in df_assigned.iterrows():
            text, cls, style, color_data = _build_block(
                row, week_start, week_end, screen_width, colors
            )

            button_id = {"type": "grid-event", "index": row.get("orig_index", idx)}
            if row.get("is_duplicate"):
                # Add a unique ``dup_idx`` flag so React keys remain unique while the
                # original ``index`` links the duplicate to its modal details.
                button_id.update({"dup": "sunday", "dup_idx": idx})

            event_blocks.append(
                html.Button(
                    html.Span(text, className="event-block-grid-text"),
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
                            "data-start": row["StartDate"].strftime(
                                "%Y-%m-%dT%H:%M:%SZ"
                            ),
                            "data-end": row["EndDate"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "data-offer": row["Offer"],
                            **color_data,
                        },
                    ),
                )
            )

    grid_fillers = [
        html.Div(
            className="grid-filler-cell",
            style={"gridRow": str(row + 1), "gridColumn": f"{col}"},
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
            style={"gridColumn": f"{i + 1}", "gridRow": f"1 / {event_rows + 1}"},
            **cast(dict[str, Any], {"data-date": date.strftime("%b %d")}),
        )
        for i, date in enumerate(dates)
    ]

    # 4. Render a single grid container containing only event blocks
    return html.Div(
        children=event_blocks + day_clickers + grid_fillers,
        className="week-grid",
    )
