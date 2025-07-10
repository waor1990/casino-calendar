from datetime import datetime, timedelta

import pandas as pd

from app_components.legacy import filter_long_spanning_events
from app_components.utils import PDT


def test_filter_long_spanning_events():
    week_start = PDT.localize(datetime(2025, 7, 6))
    week_end = week_start + timedelta(days=7)
    df = pd.DataFrame(
        {
            "EventName": ["A", "B", "C", "D"],
            "Casino": ["C"] * 4,
            "StartDate": [
                week_start - timedelta(days=1),
                week_start - timedelta(days=1),
                week_start + timedelta(days=1),
                week_start - timedelta(days=2),
            ],
            "EndDate": [
                week_end + timedelta(days=1),
                week_end - timedelta(days=1),
                week_end + timedelta(days=1),
                week_end + timedelta(hours=1),
            ],
        }
    )

    result = filter_long_spanning_events(df, week_start, week_end)
    assert list(result["EventName"]) == ["A", "D"]
