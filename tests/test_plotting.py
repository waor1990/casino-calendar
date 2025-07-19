from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objs as go
import pytest

from app_components.plotting import (
    DAY_MODAL_LABEL_REM,
    DAY_MODAL_MIN_REM,
    DAY_MODAL_TRACK_REM,
    build_weekly_figure,
    generate_day_view_html,
)
from app_components.utils import to_naive_utc
from utils.colors import get_color
from utils.data_parsing import annotate_events_with_flags, filter_week_events


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
    fig = build_weekly_figure(annot, 1024, week_start)

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

    result = generate_day_view_html(df, clicked, get_color, 1024)
    grid_style = result[1].style
    expected = max(
        DAY_MODAL_MIN_REM,
        DAY_MODAL_LABEL_REM + DAY_MODAL_TRACK_REM * 3,
    )
    assert grid_style["minWidth"] == f"{expected}rem"
