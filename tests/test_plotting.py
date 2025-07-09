from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objs as go

from app_components.legacy import build_weekly_figure
from app_components.plotting import annotate_events_with_flags, filter_week_events
from app_components.utils import PDT


def test_build_weekly_figure_structure():
    week_start = PDT.localize(datetime(2025, 4, 13))
    df = pd.DataFrame(
        {
            "EventName": ["Event"],
            "Casino": ["ilani"],
            "OfferType": ["Giveaway"],
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
