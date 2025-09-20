from datetime import datetime, timedelta

import pandas as pd
import pytest
from casino_calendar.dash_app.services import layout_state


@pytest.mark.usefixtures("casino")
def test_filter_long_spanning_events(casino):
    week_start = layout_state.to_naive_utc(datetime(2025, 7, 6))
    week_end = week_start + timedelta(days=7)
    df = pd.DataFrame(
        {
            "EventName": ["A", "B", "C", "D"],
            "Casino": [casino] * 4,
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

    result = layout_state.filter_long_spanning_events(df, week_start, week_end)
    assert list(result["EventName"]) == ["A", "D"]
