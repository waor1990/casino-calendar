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
_TIME_WORD_RE = re.compile(r"\b(?:noon|midnight)\b", re.IGNORECASE)
_TIME_RANGE_WORD_RE = re.compile(
    r"(?P<start>(?:noon|midnight|\d{1,2}(?::\d{2})?\s*(?:am|pm)?))\s*(?:-|to)\s*"
    r"(?P<end>(?:noon|midnight|\d{1,2}(?::\d{2})?\s*(?:am|pm)?))",
    re.IGNORECASE,
)

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
_WEEKDAY_TOKEN_RE = re.compile(
    r"\b(?:mon(?:day)?|tue(?:s(?:day)?)?|wed(?:nesday)?|thu(?:r(?:s(?:day)?)?)?|"
    r"fri(?:day)?|sat(?:urday)?|sun(?:day)?)s?\b",
    re.IGNORECASE,
)

_EMAIL_HEADER_RE = re.compile(
    r"^\s*(from|sent|to|cc|bcc|subject|date|reply-to|attachments?|importance)\s*:\s*.+$",
    re.IGNORECASE,
)
_EMAIL_HEADER_SEPARATOR_RE = re.compile(
    r"^\s*-{2,}\s*(?:original message|forwarded message)\s*-{2,}\s*$",
    re.IGNORECASE,
)
_EMAIL_ADDRESS_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_EMAIL_MESSAGE_RE = re.compile(r"^\s*\d+\s+messages?\s*$", re.IGNORECASE)
_EMAIL_VIEW_ONLINE_RE = re.compile(r"\bview\s+online\b", re.IGNORECASE)
_EMAIL_NAV_WORDS = {"home", "about", "gaming", "shopping", "dining", "entertainment"}
_CTA_LINE_RE = re.compile(
    r"^\s*(?:find out more|view online)(?:\s+(?:find out more|view online))*\s*$",
    re.IGNORECASE,
)
_EVENT_NAME_STOP_RE = re.compile(
    r"^\s*(?:events?\s*&\s*promotions?|events?|promotions?|free show|purchase tickets)\s*$",
    re.IGNORECASE,
)
_EVENT_NAME_SKIP_RE = re.compile(
    r"^\s*(?:"
    r"valid|must|present|visit|bring|redeem|log in|earn|you\b|you're\b|available|limit|"
    r"reservations|required|offer valid|offer is|tax|gratuity|please|pick up"
    r")\b",
    re.IGNORECASE,
)
_LIST_LINE_RE = re.compile(r"^\s*(?:[•*\-]|\d+[.)])\s+")


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

    def is_complete(self, *, allow_empty_offer: bool = False) -> bool:
        row = self.to_row()
        if allow_empty_offer:
            required = [row[0], row[1], row[2], row[4], row[5]]
        else:
            required = row
        return all(value.strip() for value in required)


@lru_cache(maxsize=1)
def _load_casino_index() -> list[dict[str, str | list[str]]]:
    lookup_path = DATA_DIR / "lookups" / "casino_index.json"
    if not lookup_path.exists():
        logger.warning("Casino index lookup missing at %s", lookup_path)
        return []
    payload = json.loads(lookup_path.read_text(encoding="utf-8"))
    entries: list[dict[str, str | list[str]]] = []
    for entry in payload:
        name = str(entry.get("name", "")).strip()
        if not name:
            continue
        entries.append(
            {
                "name": name,
                "location": str(entry.get("location", "")).strip(),
                "aliases": _build_casino_aliases(name),
            }
        )
    return entries


def _build_casino_aliases(name: str) -> list[str]:
    aliases = {name}
    lowered = name.lower()
    suffixes = [" casino", " resort casino", " resort"]
    for suffix in suffixes:
        if lowered.endswith(suffix):
            trimmed = name[: -len(suffix)].strip()
            if trimmed:
                aliases.add(trimmed)
    return sorted(aliases, key=len, reverse=True)


def parse_events_from_text(text: str, *, reference_date: date | None = None) -> list[ParsedEvent]:
    text = _strip_email_headers(text)
    casino, location = _detect_casino(text)
    if not casino:
        logger.warning("No casino match found in text; casino/location fields will be empty.")
    blocks = _split_event_blocks(text)
    if not blocks:
        raise ValueError("Promotional text is empty; no event blocks detected.")

    parsed: list[ParsedEvent] = []
    for block in blocks:
        parsed.extend(_parse_block(block, reference_date=reference_date, casino=casino, location=location))

    unique: dict[tuple[str, str, str, str, str, str], ParsedEvent] = {}
    for event in parsed:
        key = tuple(event.to_row())
        unique.setdefault(key, event)
    return list(unique.values())


def _normalize_line(line: str) -> str:
    return " ".join(line.strip().split())


def _block_lines(block: str) -> list[str]:
    raw_lines = [_normalize_line(line) for line in block.splitlines() if line.strip()]
    return _unwrap_lines(raw_lines)


def _unwrap_lines(lines: list[str]) -> list[str]:
    if not lines:
        return []
    merged: list[str] = []
    current = lines[0]
    for line in lines[1:]:
        if _should_merge_lines(current, line):
            current = _merge_lines(current, line)
        else:
            merged.append(current)
            current = line
    merged.append(current)
    return merged


def _merge_lines(current: str, line: str) -> str:
    if current.endswith("-"):
        return f"{current[:-1]}{line.lstrip()}"
    return f"{current} {line}"


def _should_merge_lines(current: str, line: str) -> bool:
    if _is_list_line(line):
        return False
    if _looks_like_title(current):
        return False
    if _is_heading_line(current):
        return _is_heading_line(line)
    if _is_heading_line(line):
        return False
    if _line_contains_date_or_time(line):
        return False
    if current.endswith((".", "!", "?", ";", ":")):
        return False
    if current.endswith((",", "-")):
        return True
    if line and line[0].islower():
        return True
    return len(current) < 60


def _strip_email_headers(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append(line)
            continue
        if _EMAIL_HEADER_RE.match(stripped):
            continue
        if _EMAIL_HEADER_SEPARATOR_RE.match(stripped):
            continue
        if stripped.lower().startswith("begin forwarded message"):
            continue
        if _EMAIL_ADDRESS_RE.search(stripped):
            continue
        if _EMAIL_MESSAGE_RE.match(stripped):
            continue
        if _EMAIL_VIEW_ONLINE_RE.search(stripped):
            continue
        if _is_email_nav_line(stripped):
            continue
        if _CTA_LINE_RE.match(_normalize_line(stripped)):
            continue
        lines.append(line)
    return "\n".join(lines)


def _is_email_nav_line(line: str) -> bool:
    words = {word.lower() for word in re.findall(r"[A-Za-z]+", line)}
    return len(words & _EMAIL_NAV_WORDS) >= 3


def _split_event_blocks(text: str) -> list[str]:
    raw_blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    if not raw_blocks:
        return []
    if not any(_block_has_date(block) for block in raw_blocks):
        return raw_blocks

    merged: list[str] = []
    current: list[str] = []
    pending: list[str] = []

    for block in raw_blocks:
        if _block_has_date(block):
            if current:
                merged.append("\n".join(current))
                current = []
            if pending:
                block = "\n".join([*pending, block])
                pending = []
            current = [block]
            continue

        if current:
            current.append(block)
        elif _is_heading_block(block):
            pending.append(block)

    if current:
        merged.append("\n".join(current))

    return merged


def _block_has_date(block: str) -> bool:
    if _DATE_TOKEN_RE.search(block):
        return True
    match = _RECURRING_RE.search(block)
    return bool(match and match.group("month"))


def _is_heading_block(block: str) -> bool:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    if not lines:
        return False
    if len(lines) > 3:
        return False
    return _is_heading_line(lines[0])


def _is_heading_line(line: str) -> bool:
    normalized = _normalize_line(line)
    letters = [char for char in normalized if char.isalpha()]
    if len(letters) < 4:
        return False
    upper = sum(1 for char in letters if char.isupper())
    return (upper / len(letters)) >= 0.6


def _is_list_line(line: str) -> bool:
    return bool(_LIST_LINE_RE.match(line))


def _looks_like_title(line: str) -> bool:
    words = re.findall(r"[A-Za-z][A-Za-z']*", line)
    if not words or len(words) > 10:
        return False
    title_words = sum(1 for word in words if word[0].isupper())
    return (title_words / len(words)) >= 0.6


def _parse_block(
    block: str,
    *,
    reference_date: date | None = None,
    casino: str | None = None,
    location: str | None = None,
) -> list[ParsedEvent]:
    reference_date = reference_date or datetime.now().date()
    if not casino:
        casino, location = _detect_casino(block)
    elif not location:
        _, location = _detect_casino(block)
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
    best_score = -1
    for entry in _load_casino_index():
        name = str(entry.get("name", ""))
        if not name:
            continue
        aliases = entry.get("aliases") or [name]
        if isinstance(aliases, str):
            aliases = [aliases]
        for alias in aliases:
            alias_text = str(alias).strip()
            if not alias_text:
                continue
            if alias_text.lower() in lower:
                score = len(alias_text)
                if score > best_score:
                    best_score = score
                    match_name = name
                    match_location = str(entry.get("location", ""))
    return match_name, match_location


def _extract_event_name(block: str, *, casino: str) -> str:
    lines = _block_lines(block)
    best_line = ""
    best_score = -999
    for line in lines:
        if casino and casino.lower() in line.lower():
            continue
        if _line_contains_date_or_time(line):
            continue
        if _EVENT_NAME_STOP_RE.match(line):
            continue
        score = _event_name_score(line)
        if score > best_score:
            best_score = score
            best_line = line
    if best_line:
        return best_line
    return lines[0] if lines else ""


def _extract_offer(block: str, *, casino: str, event_name: str) -> str:
    offer_lines: list[str] = []
    normalized_event = _normalize_line(event_name).lower() if event_name else ""
    for line in _block_lines(block):
        if not line:
            continue
        if casino and casino.lower() in line.lower():
            continue
        if normalized_event and normalized_event == _normalize_line(line).lower():
            continue
        if _EVENT_NAME_STOP_RE.match(line):
            continue
        if _line_contains_date_or_time(line):
            continue
        offer_lines.append(line)
    offer = " ".join(offer_lines).strip()
    if offer:
        offer = _strip_dates_and_times(offer)
    return offer


def _event_name_score(line: str) -> int:
    score = 0
    words = line.split()
    if _is_heading_line(line):
        score += 4
    if _looks_like_title(line):
        score += 2
    if "$" in line or any(char.isdigit() for char in line):
        score += 2
    if 2 <= len(words) <= 8:
        score += 2
    elif len(words) > 14:
        score -= 2
    if line.endswith("."):
        score -= 2
    if _EVENT_NAME_SKIP_RE.match(line):
        score -= 4
    return score


def _line_contains_date_or_time(line: str) -> bool:
    lowered = line.lower()
    return bool(
        _DATE_TOKEN_RE.search(lowered)
        or _TIME_RANGE_RE.search(lowered)
        or _TIME_RANGE_WORD_RE.search(lowered)
        or _TIME_RE.search(lowered)
        or _TIME_24_RE.search(lowered)
        or _TIME_WORD_RE.search(lowered)
        or _WEEKDAY_TOKEN_RE.search(lowered)
    )


def _strip_dates_and_times(value: str) -> str:
    value = _DATE_TOKEN_RE.sub("", value)
    value = _TIME_RANGE_RE.sub("", value)
    value = _TIME_RANGE_WORD_RE.sub("", value)
    value = _TIME_RE.sub("", value)
    value = _TIME_24_RE.sub("", value)
    value = _TIME_WORD_RE.sub("", value)
    value = _WEEKDAY_TOKEN_RE.sub("", value)
    return " ".join(value.split())


def _extract_time_range(block: str) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    match = _TIME_RANGE_WORD_RE.search(block)
    if match:
        start_text = match.group("start")
        end_text = match.group("end")
        try:
            start_time, start_meridiem = _parse_time(start_text)
            end_time, _ = _parse_time(end_text, default_meridiem=start_meridiem)
        except ValueError as exc:
            logger.warning("Ignoring invalid time range '%s' - '%s': %s", start_text, end_text, exc)
            return None, None
        return start_time, end_time

    match = _TIME_RANGE_RE.search(block)
    if match:
        start_text = match.group("start")
        end_text = match.group("end")
        try:
            start_time, start_meridiem = _parse_time(start_text)
            end_time, _ = _parse_time(end_text, default_meridiem=start_meridiem)
        except ValueError as exc:
            logger.warning("Ignoring invalid time range '%s' - '%s': %s", start_text, end_text, exc)
            return None, None
        return start_time, end_time

    match = _TIME_RE.search(block)
    if match:
        try:
            start_time, _ = _parse_time(match.group(0))
        except ValueError as exc:
            logger.warning("Ignoring invalid time '%s': %s", match.group(0), exc)
            return None, None
        return start_time, start_time

    match = _TIME_24_RE.search(block)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2) or 0)
        return (hours, minutes), (hours, minutes)

    match = _TIME_WORD_RE.search(block)
    if match:
        try:
            start_time, _ = _parse_time(match.group(0))
        except ValueError as exc:
            logger.warning("Ignoring invalid time '%s': %s", match.group(0), exc)
            return None, None
        return start_time, start_time

    return None, None


def _parse_time(value: str, default_meridiem: str | None = None) -> tuple[tuple[int, int], str | None]:
    normalized = value.strip().lower()
    if normalized == "noon":
        return (12, 0), None
    if normalized == "midnight":
        return (0, 0), None

    match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*([ap]m)?", value.strip(), re.IGNORECASE)
    if not match:
        raise ValueError(f"Unrecognized time format: {value}")
    hours = int(match.group(1))
    minutes = int(match.group(2) or 0)
    meridiem = match.group(3).lower() if match.group(3) else None
    if not meridiem and default_meridiem:
        meridiem = default_meridiem
    if minutes > 59:
        raise ValueError(f"Invalid minutes value: {minutes}")
    if meridiem:
        if hours < 1 or hours > 12:
            raise ValueError(f"Invalid 12-hour value: {hours}")
        if hours == 12:
            hours = 0
        if meridiem == "pm":
            hours += 12
    elif hours > 23:
        raise ValueError(f"Invalid 24-hour value: {hours}")
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
