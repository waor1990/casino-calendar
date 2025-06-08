from datetime import datetime, timedelta
from typing import Tuple

from pytz import timezone

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
    localized = clicked_date.astimezone(tz)
    naive = localized.replace(tzinfo=None)

    start_naive = (naive - timedelta(days=(naive.weekday() + 1) % 7)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    week_start = tz.localize(start_naive, is_dst=None)
    week_end = tz.normalize(week_start + timedelta(days=7))

    return week_start, week_end
