from datetime import datetime, timedelta

from app_components.utils import PDT
from app_components.week_grid_layout import _build_block

LONG_TEXT = "This is a very long event name for overflow testing"


def _row(start, end):
    return {
        "EventName": LONG_TEXT,
        "OfferType": "Giveaway",
        "Casino": "ilani",
        "row_num": 0,
        "StartDate": start,
        "EndDate": end,
        "has_left_arrow": False,
        "has_right_arrow": False,
    }


COLORS = {"ilani": {"bg": "#fff", "text": "#000"}}


def test_build_block_adds_ellipsis_on_narrow_screen():
    week_start = PDT.localize(datetime(2025, 7, 6))
    week_end = week_start + timedelta(days=7)
    row = _row(week_start + timedelta(days=1), week_start + timedelta(days=2))

    text, _, _ = _build_block(row, week_start, week_end, 375, COLORS)
    assert text.endswith("...")


def test_build_block_uses_emoji_when_too_small():
    week_start = PDT.localize(datetime(2025, 7, 6))
    week_end = week_start + timedelta(days=7)
    row = _row(week_start + timedelta(days=1), week_start + timedelta(days=2))

    text, _, _ = _build_block(row, week_start, week_end, 100, COLORS)
    assert text == "🎁🎰"
