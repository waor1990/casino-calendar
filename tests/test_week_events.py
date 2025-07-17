from datetime import datetime, timedelta

import pandas as pd
import pytest

from app_components.utils import to_naive_utc
from utils.data_parsing import prepare_week_events


@pytest.mark.usefixtures("casino")
def test_prepare_week_events_flags_boundary_events(casino):
    week_start = to_naive_utc(datetime(2025, 7, 6))
    df = pd.DataFrame(
        {
            "EventName": ["Left", "Right", "Full"],
            "Casino": [casino] * 3,
            "StartDate": [
                week_start - timedelta(days=1),
                week_start + timedelta(days=5),
                week_start - timedelta(days=1),
            ],
            "EndDate": [
                week_start + timedelta(hours=2),
                week_start + timedelta(days=7, hours=2),
                week_start + timedelta(days=8),
            ],
        }
    )

    result = prepare_week_events(df, week_start)

    names = list(result["EventName"])
    assert names == ["Left", "Right"]

    left = result[result["EventName"] == "Left"].iloc[0]
    right = result[result["EventName"] == "Right"].iloc[0]

    assert left["has_left_arrow"] and not left["has_right_arrow"]
    assert right["has_right_arrow"] and not right["has_left_arrow"]
