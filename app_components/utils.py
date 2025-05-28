from datetime import datetime, timedelta
from pytz import timezone
from typing import Tuple

PDT = timezone('America/Los_Angeles')

def get_week_range(clicked_date: datetime) -> Tuple[datetime, datetime]:
    week_start = clicked_date - timedelta(days=(clicked_date.weekday() + 1) % 7)
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0), week_start + timedelta(days=7)

