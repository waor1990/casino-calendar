from datetime import datetime, timedelta

import pytest
from app_components.utils import offer_type_emoji, to_naive_utc
from app_components.week_grid_layout import _build_block

LONG_TEXT = "This is a very long event name for overflow testing"


def _row(start, end, casino: str, offer: str) -> dict:
    return {
        "EventName": LONG_TEXT,
        "OfferType": offer,
        "Casino": casino,
        "row_num": 0,
        "StartDate": start,
        "EndDate": end,
        "has_left_arrow": False,
        "has_right_arrow": False,
    }


COLORS = {
    "ilani": {"bg": "#fff", "text": "#000"},
    "Lucky Eagle Casino": {"bg": "#fff", "text": "#000"},
}


@pytest.mark.usefixtures("offer_type", "casino")
def test_build_block_adds_ellipsis_on_narrow_screen(casino, offer_type):
    week_start = to_naive_utc(datetime(2025, 7, 6))
    week_end = week_start + timedelta(days=7)
    row = _row(
        week_start + timedelta(days=1),
        week_start + timedelta(days=2),
        casino,
        offer_type,
    )

    text, _, _ = _build_block(row, week_start, week_end, 375, COLORS)
    assert text.endswith("...")


@pytest.mark.usefixtures("offer_type", "casino")
def test_build_block_uses_emoji_when_too_small(casino, offer_type):
    week_start = to_naive_utc(datetime(2025, 7, 6))
    week_end = week_start + timedelta(days=7)
    row = _row(
        week_start + timedelta(days=1),
        week_start + timedelta(days=2),
        casino,
        offer_type,
    )

    text, _, _ = _build_block(row, week_start, week_end, 100, COLORS)
    assert text == offer_type_emoji(offer_type)
