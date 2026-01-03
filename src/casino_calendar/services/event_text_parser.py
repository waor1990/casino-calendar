"""Parse promotional text into structured casino event fields."""

from __future__ import annotations

import calendar
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from typing import Iterable

from casino_calendar.logging.config import setup_logger
from casino_calendar.settings import DATA_DIR

logger = setup_logger(__name__)

REQUIRED_FIELDS = ["EventName", "Casino", "Location", "Offer", "StartDate", "EndDate"]

_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_TIME_RANGE_RE = re.compile(
    r"(?P<start>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:-|–|to)\s*" r"(?P<end>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
    re.IGNORECASE,
)
_TIME_RE = re.compile(r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b", re.IGNORECASE)
_TIME_24_RE = re.compile(r"\b([01]?\d|2[0-3])(?::([0-5]\d))\b")

_MONTH_DATE_RE = re.compile(
    r"\b(?P<month>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"\s+(?P<start>\d{1,2})(?:\s*(?:-|–|to|through|thru)\s*(?P<end>\d{1,2}))?"
    r"(?:,\s*(?P<year>\d{4}))?",
    re.IGNORECASE,
)
_NUMERIC_DATE_RE = re.compile(r"\b(?P<month>\d{1,2})/(?P<day>\d{1,2})(?:/(?P<year>\d{2,4}))?\b")
_NUMERIC_RANGE_RE = re.compile(
    r"\b(?P<start_month>\d{1,2})/(?P<start_day>\d{1,2})(?:/(?P<start_year>\d{2,4}))?"
    r"\s*(?:-|–|to|through|thru)\s*(?P<end_month>\d{1,2})/(?P<end_day>\d{1,2})"
    r"(?:/(?P<end_year>\d{2,4}))?\b"
)
_RECURRING_RE = re.compile(
    r"\b(?:every|each)\s+(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
    r"(?:\s+(?:in|during)\s+(?P<month>[A-Za-z]+)\s*(?P<year>\d{4})?)?",
    re.IGNORECASE,
)

_DATE_TOKEN_RE = re.compile(
    r"\b("
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"\s+\d{1,2}(?:\s*(?:-|–|to|through|thru)\s*\d{1,2})?(?:,\s*\d{4})?"
    r"|\d{1,2}/\d{1,2}(?:/\d{2,4})?"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedEvent:
    event_name: str
    casino: str
    location: str
    offer: str
    start: datetime | None
    end: datetime | None

    def to_row(self) -> list[str]:
        return [
            self.event_name,
            self.casino,
            self.location,
            self.offer,
            _format_datetime(self.start),
            _format_datetime(self.end),
        ]

    def to_payload(self) -> dict[str, str]:
        return dict(zip(REQUIRED_FIELDS, self.to_row(), strict=True))


@lru_cache(maxsize=1)
def _load_casino_index() -> list[dict[str, str]]:
    lookup_path = DATA_DIR / "lookups" / "casino_index.json"
    if not lookup_path.exists():
        logger.warning("Casino index lookup missing at %s", lookup_path)
        return []
    payload = json.loads(lookup_path.read_text(encoding="utf-8"))
    entries: list[dict[str, str]] = []
    for entry in payload:
        name = str(entry.get("name", "")).strip()
        if not name:
            continue
        entries.append({"name": name, "location": str(entry.get("location", "")).strip()})
    return entries


def parse_events_from_text(text: str, *, reference_date: date | None = None) -> list[ParsedEvent]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    if not blocks:
        raise ValueError("Promotional text is empty; no event blocks detected.")

    parsed: list[ParsedEvent] = []
    for block in blocks:
        parsed.extend(_parse_block(block, reference_date=reference_date))

    unique: dict[tuple[str, str, str, str, str, str], ParsedEvent] = {}
    for event in parsed:
        key = tuple(event.to_row())
        unique.setdefault(key, event)
    return list(unique.values())


def _parse_block(block: str, *, reference_date: date | None = None) -> list[ParsedEvent]:
    reference_date = reference_date or datetime.now().date()
    casino, location = _detect_casino(block)
    time_range = _extract_time_range(block)
    dates = _extract_dates(block, reference_date=reference_date)

    event_name = _extract_event_name(block, casino=casino)
    offer = _extract_offer(block, casino=casino, event_name=event_name)

    if not dates:
        start_dt, end_dt = _apply_time_to_date(None, time_range)
        return [
            ParsedEvent(
                event_name=event_name,
                casino=casino,
                location=location,
                offer=offer,
                start=start_dt,
                end=end_dt,
            )
        ]

    events: list[ParsedEvent] = []
    for start_date, end_date in dates:
        start_dt, end_dt = _apply_time_to_date(start_date, time_range, end_date=end_date)
        events.append(
            ParsedEvent(
                event_name=event_name,
                casino=casino,
                location=location,
                offer=offer,
                start=start_dt,
                end=end_dt,
            )
        )
    return events


def _detect_casino(block: str) -> tuple[str, str]:
    lower = block.lower()
    match_name = ""
    match_location = ""
    for entry in sorted(_load_casino_index(), key=lambda item: len(item["name"]), reverse=True):
        name = entry["name"]
        if name.lower() in lower:
            match_name = name
            match_location = entry.get("location", "")
            break
    return match_name, match_location


def _extract_event_name(block: str, *, casino: str) -> str:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    for line in lines:
        if casino and casino.lower() in line.lower():
            continue
        if _line_contains_date_or_time(line):
            continue
        return line
    return lines[0] if lines else ""


def _extract_offer(block: str, *, casino: str, event_name: str) -> str:
    offer_lines: list[str] = []
    for line in (line.strip() for line in block.splitlines()):
        if not line:
            continue
        if casino and casino.lower() in line.lower():
            continue
        if event_name and event_name.lower() == line.lower():
            continue
        if _line_contains_date_or_time(line):
            continue
        offer_lines.append(line)
    offer = " ".join(offer_lines).strip()
    if offer:
        offer = _strip_dates_and_times(offer)
    return offer


def _line_contains_date_or_time(line: str) -> bool:
    lowered = line.lower()
    return bool(
        _DATE_TOKEN_RE.search(lowered)
        or _TIME_RANGE_RE.search(lowered)
        or _TIME_RE.search(lowered)
        or _TIME_24_RE.search(lowered)
        or any(day in lowered for day in _WEEKDAYS)
    )


def _strip_dates_and_times(value: str) -> str:
    value = _DATE_TOKEN_RE.sub("", value)
    value = _TIME_RANGE_RE.sub("", value)
    value = _TIME_RE.sub("", value)
    value = _TIME_24_RE.sub("", value)
    return " ".join(value.split())


def _extract_time_range(block: str) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    match = _TIME_RANGE_RE.search(block)
    if match:
        start_text = match.group("start")
        end_text = match.group("end")
        start_time, start_meridiem = _parse_time(start_text)
        end_time, _ = _parse_time(end_text, default_meridiem=start_meridiem)
        return start_time, end_time

    match = _TIME_RE.search(block)
    if match:
        start_time, _ = _parse_time(match.group(0))
        return start_time, start_time

    match = _TIME_24_RE.search(block)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2) or 0)
        return (hours, minutes), (hours, minutes)

    return None, None


def _parse_time(value: str, default_meridiem: str | None = None) -> tuple[tuple[int, int], str | None]:
    match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*([ap]m)?", value.strip(), re.IGNORECASE)
    if not match:
        raise ValueError(f"Unrecognized time format: {value}")
    hours = int(match.group(1))
    minutes = int(match.group(2) or 0)
    meridiem = match.group(3).lower() if match.group(3) else None
    if not meridiem and default_meridiem:
        meridiem = default_meridiem
    if meridiem:
        if hours == 12:
            hours = 0
        if meridiem == "pm":
            hours += 12
    return (hours, minutes), meridiem


def _extract_dates(block: str, *, reference_date: date) -> list[tuple[date, date]]:
    recurring = _extract_recurring_dates(block, reference_date=reference_date)
    if recurring:
        return [(day, day) for day in recurring]

    spans: list[tuple[int, int]] = []
    ranges: list[tuple[date, date]] = []

    for match in _NUMERIC_RANGE_RE.finditer(block):
        start_year = _normalize_year(match.group("start_year"), reference_date.year)
        end_year = _normalize_year(match.group("end_year"), start_year)
        start_date = date(start_year, int(match.group("start_month")), int(match.group("start_day")))
        end_date = date(end_year, int(match.group("end_month")), int(match.group("end_day")))
        ranges.append((start_date, end_date))
        spans.append(match.span())

    for match in _MONTH_DATE_RE.finditer(block):
        month_value = _month_from_token(match.group("month"))
        start_day = int(match.group("start"))
        end_day = int(match.group("end") or start_day)
        year_value = _normalize_year(match.group("year"), reference_date.year)
        start_date = date(year_value, month_value, start_day)
        end_date = date(year_value, month_value, end_day)
        ranges.append((start_date, end_date))
        spans.append(match.span())

    singles: list[date] = []
    for match in _NUMERIC_DATE_RE.finditer(block):
        if _span_overlaps(match.span(), spans):
            continue
        month_value = int(match.group("month"))
        day_value = int(match.group("day"))
        year_value = _normalize_year(match.group("year"), reference_date.year)
        singles.append(date(year_value, month_value, day_value))

    dates: list[tuple[date, date]] = []
    dates.extend(ranges)
    dates.extend((single, single) for single in singles)
    return dates


def _extract_recurring_dates(block: str, *, reference_date: date) -> list[date]:
    match = _RECURRING_RE.search(block)
    if not match:
        return []
    weekday = match.group("weekday")
    month_token = match.group("month")
    if not weekday or not month_token:
        return []
    month_value = _month_from_token(month_token)
    year_value = _normalize_year(match.group("year"), reference_date.year)
    return _weekday_dates_for_month(year_value, month_value, _WEEKDAYS[weekday.lower()])


def _weekday_dates_for_month(year: int, month: int, weekday_index: int) -> list[date]:
    _, total_days = calendar.monthrange(year, month)
    return [
        date(year, month, day) for day in range(1, total_days + 1) if date(year, month, day).weekday() == weekday_index
    ]


def _apply_time_to_date(
    start_date: date | None,
    time_range: tuple[tuple[int, int] | None, tuple[int, int] | None],
    *,
    end_date: date | None = None,
) -> tuple[datetime | None, datetime | None]:
    start_time, end_time = time_range
    if start_date is None:
        return None, None
    if end_date is None:
        end_date = start_date
    if start_time is None or end_time is None:
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.min.time()).replace(hour=23, minute=59)
        return start_dt, end_dt
    start_dt = datetime.combine(start_date, datetime.min.time()).replace(hour=start_time[0], minute=start_time[1])
    end_dt = datetime.combine(end_date, datetime.min.time()).replace(hour=end_time[0], minute=end_time[1])
    return start_dt, end_dt


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return ""
    return f"{value.month}/{value.day}/{value.year} {value.hour:02d}:{value.minute:02d}"


def _normalize_year(value: str | None, default_year: int) -> int:
    if not value:
        return default_year
    year = int(value)
    return year + 2000 if year < 100 else year


def _month_from_token(token: str) -> int:
    key = token.strip().lower()
    if key.isdigit():
        return int(key)
    month_value = _MONTHS.get(key)
    if not month_value:
        raise ValueError(f"Unknown month token: {token}")
    return month_value


def _span_overlaps(span: tuple[int, int], spans: Iterable[tuple[int, int]]) -> bool:
    for existing in spans:
        if span[0] < existing[1] and existing[0] < span[1]:
            return True
    return False
