from datetime import datetime, timedelta

import pytest
from app_components.utils import to_naive_utc
from app_components.week_grid_layout import _build_block


@pytest.mark.usefixtures("casino")
def test_build_block_breakpoints(casino):
    week_start = to_naive_utc(datetime(2025, 7, 6))
    week_end = week_start + timedelta(days=7)
    row = {
        "EventName": "This is a very long event name for testing breakpoints",
        "Casino": casino,
        "row_num": 0,
        "StartDate": week_start + timedelta(days=1),
        "EndDate": week_start + timedelta(days=3),
        "has_left_arrow": False,
        "has_right_arrow": False,
    }
    colors = {casino: {"bg": "#fff", "text": "#000"}}

    mobile_text, _, _ = _build_block(row, week_start, week_end, 375, colors)
    tablet_text, _, _ = _build_block(row, week_start, week_end, 650, colors)
    desktop_text, _, _ = _build_block(row, week_start, week_end, 1024, colors)

    assert len(mobile_text) <= len(tablet_text) <= len(desktop_text)
