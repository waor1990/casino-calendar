from datetime import datetime

from casino_calendar.dash_app.services import layout_state


def test_get_week_range_returns_sunday_bounds():
    dt = layout_state.PDT.localize(datetime(2025, 4, 16, 15, 0))
    start, end = layout_state.get_week_range(dt)
    start_pdt = layout_state.to_pdt(start)
    assert start_pdt.weekday() == 6
    assert start_pdt.hour == 0
    assert start.tzinfo is None
    assert (end - start).days == 7


def test_get_week_range_handles_naive_datetime():
    dt = datetime(2025, 4, 16, 15, 0)
    start, _ = layout_state.get_week_range(dt)
    assert start.tzinfo is None


def test_trim_label_truncates_and_emojis():
    text = "This is a very long label"
    assert layout_state.trim_label(text, 10, "Giveaway").endswith("...")
    assert layout_state.trim_label(
        text, 3, "Giveaway"
    ) == layout_state.offer_type_emoji("Giveaway")


def test_offer_type_emoji_default():
    assert layout_state.offer_type_emoji("Unknown") == "..."
