from datetime import datetime, timedelta
from typing import Any, Iterable, Tuple

import pandas as pd
from casino_calendar.services.config_cache import get_config
from casino_calendar.settings import APP_TIMEZONE, UTC_TZ
from dash import html


def offer_type_emoji(offer_type: str) -> str:
    """Return emoji for the given ``offer_type`` or ellipsis for unknown."""
    emojis = get_config("lookups/offer_type_emojis.json") or {}
    return emojis.get(offer_type, "...")


PDT = APP_TIMEZONE


def to_naive_utc(dt: datetime) -> datetime:
    """Return ``dt`` converted to naive UTC."""

    if dt.tzinfo is None:
        localized = PDT.localize(dt)
    else:
        localized = dt
    return localized.astimezone(UTC_TZ).replace(tzinfo=None)


def to_pdt(dt: datetime) -> datetime:
    """Return ``dt`` converted from naive UTC to aware PDT."""

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(PDT)


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
        localized = PDT.localize(clicked_date)
    else:
        localized = clicked_date.astimezone(tz)

    week_start_local = (localized - timedelta(days=(localized.weekday() + 1) % 7)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_end_local = week_start_local + timedelta(days=7)

    week_start = week_start_local.astimezone(UTC_TZ).replace(tzinfo=None)
    week_end = week_end_local.astimezone(UTC_TZ).replace(tzinfo=None)

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


def filter_long_spanning_events(
    events_df: pd.DataFrame,
    week_start: datetime,
    week_end: datetime,
) -> pd.DataFrame:
    """Return events that span the entire week."""

    return events_df[(events_df["StartDate"] < week_start) & (events_df["EndDate"] > week_end)].copy()


def build_event_info_rows(data: Iterable[tuple[str, Any]]) -> list[Any]:
    """Return HTML rows for event details given a ``data`` iterable."""

    mapping = dict(data)
    emoji = offer_type_emoji(mapping.get("OfferType", ""))
    rows: list[Any] = [html.H2(f"{emoji} Event Detail {emoji}", className="event-label-title")]

    for label in [
        "EventName",
        "Casino",
        "OfferType",
        "StartDate",
        "EndDate",
        "Offer",
    ]:
        if label in mapping:
            display_label = {
                "EventName": "Name of Event",
                "StartDate": "Start of Event",
                "EndDate": "End of Event",
                "OfferType": "Offer Type",
            }.get(label, label)

            value = mapping[label]
            if label in ["StartDate", "EndDate"]:
                try:
                    ts = pd.to_datetime(value)
                    value = to_pdt(ts).strftime("%b %d, %Y @ %I:%M %p")
                except Exception:
                    pass

            rows.append(
                html.Div(
                    [html.Strong(f"{display_label}: "), html.Span(value)],
                    className="event-label",
                )
            )

    return rows
