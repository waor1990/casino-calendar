from datetime import datetime, timedelta
from typing import Tuple

from pytz import timezone

OFFER_TYPE_EMOJIS = {
    "Free-Play": "🎰💵",
    "Hospitality-Rewards": "🏨🎲",
    "Point-Based": "📈💯",
    "Giveaway": "🎁🎰",
    "Special-Events": "🎲💵",
    "Offer": "🎁❓",
}


def offer_type_emoji(offer_type: str) -> str:
    """Return emoji for the given ``offer_type`` or ellipsis for unknown."""

    return OFFER_TYPE_EMOJIS.get(offer_type, "...")


PDT = timezone("America/Los_Angeles")


def get_week_range(clicked_date: datetime) -> Tuple[datetime, datetime]:
    """Return the start and end datetimes (inclusive/exclusive) for the week.

    The calculation accounts for daylight saving time transitions by
    constructing naive datetimes and localizing them through ``pytz``.  This
    avoids errors where the offset from ``clicked_date`` would otherwise be
    applied to the entire week when simply adding/subtracting ``timedelta``
    objects.
    """

    tz = clicked_date.tzinfo or PDT
    if clicked_date.tzinfo is None:
        localized = tz.localize(clicked_date)
    else:
        localized = clicked_date.astimezone(tz)

    week_start = (localized - timedelta(days=(localized.weekday() + 1) % 7)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_end = week_start + timedelta(days=7)

    return week_start, week_end


def trim_label(label: str, max_chars: int, offer_type: str = "") -> str:
    """Return ``label`` truncated to ``max_chars``.

    If the label must be truncated and ``max_chars`` is at least ``4``,
    append an ellipsis after the last full word that fits.  For very
    small ``max_chars`` values (<4), return an emoji representing the
    ``offer_type`` instead of an ellipsis.
    """

    emoji = offer_type_emoji(offer_type)

    if len(label) <= max_chars:
        return label

    if max_chars < 4:
        return emoji

    allowed = max_chars - 3
    words = label.split()
    trimmed = ""
    for word in words:
        candidate = f"{trimmed} {word}".strip()
        if len(candidate) > allowed:
            break
        trimmed = candidate

    if not trimmed:
        return emoji

    return f"{trimmed}..."


def max_chars_for_span(span_days: float, screen_width: int) -> int:
    """Return the character count that fits within ``span_days`` on ``screen_width``.

    The calculation approximates the width of an average character to
    determine how many characters can be displayed without overflowing the
    event block.
    """

    font_px = (
        12
        if screen_width < 480
        else 14 if screen_width < 768 else 16 if screen_width < 1024 else 18
    )
    approx_char_px = font_px * 0.6
    block_px = screen_width * (span_days / 7) * 0.95
    return max(int(block_px / approx_char_px), 0)
