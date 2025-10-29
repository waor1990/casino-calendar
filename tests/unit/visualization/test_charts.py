from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objs as go
import pytest
from casino_calendar.dash_app.services.layout_state import to_naive_utc
from casino_calendar.dash_app.visualization import charts as day_charts
from casino_calendar.services.colors import get_color
from casino_calendar.services.data_parsing import (
    annotate_events_with_flags,
    filter_week_events,
)


@pytest.mark.usefixtures("casino", "offer_type")
def test_build_weekly_figure_structure(casino, offer_type):
    week_start = to_naive_utc(datetime(2025, 4, 13))
    df = pd.DataFrame(
        {
            "EventName": ["Event"],
            "Casino": [casino],
            "OfferType": [offer_type],
            "StartDate": [week_start + timedelta(days=1, hours=2)],
            "EndDate": [week_start + timedelta(days=1, hours=4)],
        }
    )

    events = filter_week_events(df, week_start, week_start + timedelta(days=7))
    annot = annotate_events_with_flags(
        events, week_start, week_start + timedelta(days=7)
    )
    fig = day_charts.build_weekly_figure(annot, 1024, week_start)

    assert isinstance(fig, go.Figure)
    assert fig.layout.shapes
    assert fig.data
    assert len(fig.layout.xaxis.ticktext) == 7


def test_generate_day_view_width_scales_with_tracks():
    clicked = to_naive_utc(datetime(2025, 7, 12))
    df = pd.DataFrame(
        {
            "EventName": ["A", "B", "C"],
            "Casino": ["ilani"] * 3,
            "OfferType": ["", "", ""],
            "Offer": ["", "", ""],
            "StartDate": [
                clicked.replace(hour=10),
                clicked.replace(hour=10, minute=30),
                clicked.replace(hour=11),
            ],
            "EndDate": [
                clicked.replace(hour=12),
                clicked.replace(hour=13),
                clicked.replace(hour=12, minute=30),
            ],
        }
    )

    result = day_charts.generate_day_view_html(df, clicked, get_color, 1024)
    grid_style = result[1].style
    char_rem = 0.55
    max_len = max(len(n) for n in df["EventName"])
    expected = max(
        day_charts.DAY_MODAL_WIDE_REM,
        day_charts.DAY_MODAL_LABEL_REM + day_charts.DAY_MODAL_TRACK_REM * 3,
        day_charts.DAY_MODAL_LABEL_REM + char_rem * (max_len + 2) * 3,
    )
    assert grid_style["minWidth"] == f"{expected}rem"


def test_event_block_min_width_for_few_events():
    clicked = to_naive_utc(datetime(2025, 8, 5))
    df = pd.DataFrame(
        {
            "EventName": [
                "Very Long Event Name One",
                "Another Extremely Long Event Name",
            ],
            "Casino": ["ilani", "ilani"],
            "OfferType": ["", ""],
            "Offer": ["", ""],
            "StartDate": [
                clicked.replace(hour=9),
                clicked.replace(hour=12),
            ],
            "EndDate": [
                clicked.replace(hour=10),
                clicked.replace(hour=13),
            ],
        }
    )

    result = day_charts.generate_day_view_html(df, clicked, get_color, 1024)
    grid_children = result[1].children
    event_divs = [
        c
        for c in grid_children
        if getattr(c, "className", "") and "event-block-day" in c.className
    ]

    assert len(event_divs) == 2
    for div, name in zip(event_divs, df["EventName"], strict=False):
        expected_width = f"{len(name) + 2}ch"
        min_width = div.style.get("minWidth")
        if min_width.endswith("ch"):
            assert min_width == expected_width
        else:
            assert min_width.endswith("%")


def test_day_view_includes_overlapping_events():
    sunday = to_naive_utc(datetime(2025, 7, 13))
    df = pd.DataFrame(
        {
            "EventName": ["Span1", "Span2"],
            "Casino": ["ilani", "ilani"],
            "OfferType": ["", ""],
            "Offer": ["", ""],
            "StartDate": [
                sunday - timedelta(hours=2),
                sunday + timedelta(hours=22),
            ],
            "EndDate": [
                sunday + timedelta(days=1, hours=1),
                sunday + timedelta(days=1, hours=2),
            ],
        }
    )

    sun_result = day_charts.generate_day_view_html(df, sunday, get_color, 1024)
    mon_result = day_charts.generate_day_view_html(
        df, sunday + timedelta(days=1), get_color, 1024
    )

    for result in (sun_result, mon_result):
        grid_children = result[1].children
        event_divs = [
            c
            for c in grid_children
            if getattr(c, "className", "") and "event-block-day" in c.className
        ]
        assert len(event_divs) == 2


def test_short_events_near_midnight_do_not_overlap_or_overflow():
    clicked = to_naive_utc(datetime(2025, 8, 5))
    df = pd.DataFrame(
        {
            "EventName": ["Late1", "Late2"],
            "Casino": ["ilani", "ilani"],
            "OfferType": ["", ""],
            "Offer": ["", ""],
            "StartDate": [
                clicked.replace(hour=6, minute=50) + timedelta(days=1),
                clicked.replace(hour=6, minute=55) + timedelta(days=1),
            ],
            "EndDate": [
                clicked.replace(hour=6, minute=55) + timedelta(days=1),
                clicked.replace(hour=7) + timedelta(days=1),
            ],
        }
    )

    result = day_charts.generate_day_view_html(df, clicked, get_color, 1024)
    grid_children = result[1].children
    event_divs = [
        c
        for c in grid_children
        if getattr(c, "className", "") and "event-block-day" in c.className
    ]
    assert len(event_divs) == 2

    hour_height, _ = day_charts.get_layout_config(1024)
    total_height = 24 * hour_height
    lefts = set()
    for div in event_divs:
        top = float(div.style.get("top", "0px").rstrip("px"))
        height = float(div.style.get("height", "0px").rstrip("px"))
        assert top >= 0
        assert top + height <= total_height
        lefts.add(div.style.get("left"))

    assert len(lefts) == 2, "Events should occupy separate tracks"
