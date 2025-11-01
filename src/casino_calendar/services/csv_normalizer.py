"""Utilities for normalising raw casino event CSV files for the Dash app."""

from __future__ import annotations

import csv
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from pathlib import Path
from typing import Iterable, Sequence

from casino_calendar.logging import config as logging_config

logger = logging_config.setup_maintenance_logger(
    "casino_calendar.services.csv_normalizer"
)

DEFAULT_OUTPUT_PATH = Path("data") / "raw" / "casino_events.csv"
EXPECTED_COLUMNS = ["EventName", "Casino", "Location", "Offer", "StartDate", "EndDate"]

_EXCEL_EPOCH = datetime(1899, 12, 30)

_CATEGORY_EVENT = "event"
_CATEGORY_CASINO = "casino"
_CATEGORY_LOCATION_PRIMARY = "location_primary"
_CATEGORY_LOCATION_PART = "location_part"
_CATEGORY_OFFER = "offer"
_CATEGORY_OFFER_EXTRA = "offer_extra"
_CATEGORY_START_DATETIME = "start_datetime"
_CATEGORY_START_DATE = "start_date"
_CATEGORY_START_TIME = "start_time"
_CATEGORY_END_DATETIME = "end_datetime"
_CATEGORY_END_DATE = "end_date"
_CATEGORY_END_TIME = "end_time"

_HEADER_CATEGORY_MAP = {
    "event": _CATEGORY_EVENT,
    "eventname": _CATEGORY_EVENT,
    "eventtitle": _CATEGORY_EVENT,
    "title": _CATEGORY_EVENT,
    "name": _CATEGORY_EVENT,
    "casinoname": _CATEGORY_CASINO,
    "casino": _CATEGORY_CASINO,
    "property": _CATEGORY_CASINO,
    "propertyname": _CATEGORY_CASINO,
    "resort": _CATEGORY_CASINO,
    "brand": _CATEGORY_CASINO,
    "location": _CATEGORY_LOCATION_PRIMARY,
    "venue": _CATEGORY_LOCATION_PRIMARY,
    "room": _CATEGORY_LOCATION_PRIMARY,
    "area": _CATEGORY_LOCATION_PRIMARY,
    "address": _CATEGORY_LOCATION_PART,
    "street": _CATEGORY_LOCATION_PART,
    "city": _CATEGORY_LOCATION_PART,
    "state": _CATEGORY_LOCATION_PART,
    "province": _CATEGORY_LOCATION_PART,
    "zip": _CATEGORY_LOCATION_PART,
    "zipcode": _CATEGORY_LOCATION_PART,
    "postalcode": _CATEGORY_LOCATION_PART,
    "country": _CATEGORY_LOCATION_PART,
    "offer": _CATEGORY_OFFER,
    "offertitle": _CATEGORY_OFFER,
    "offername": _CATEGORY_OFFER,
    "promotion": _CATEGORY_OFFER,
    "promo": _CATEGORY_OFFER,
    "giveaway": _CATEGORY_OFFER,
    "details": _CATEGORY_OFFER_EXTRA,
    "detail": _CATEGORY_OFFER_EXTRA,
    "description": _CATEGORY_OFFER_EXTRA,
    "notes": _CATEGORY_OFFER_EXTRA,
    "note": _CATEGORY_OFFER_EXTRA,
    "disclaimer": _CATEGORY_OFFER_EXTRA,
    "summary": _CATEGORY_OFFER_EXTRA,
    "startdatetime": _CATEGORY_START_DATETIME,
    "startdt": _CATEGORY_START_DATETIME,
    "start": _CATEGORY_START_DATETIME,
    "begin": _CATEGORY_START_DATETIME,
    "startdate": _CATEGORY_START_DATE,
    "begindate": _CATEGORY_START_DATE,
    "startday": _CATEGORY_START_DATE,
    "starttime": _CATEGORY_START_TIME,
    "begintime": _CATEGORY_START_TIME,
    "starthour": _CATEGORY_START_TIME,
    "enddatetime": _CATEGORY_END_DATETIME,
    "enddt": _CATEGORY_END_DATETIME,
    "end": _CATEGORY_END_DATETIME,
    "finish": _CATEGORY_END_DATETIME,
    "enddate": _CATEGORY_END_DATE,
    "finishdate": _CATEGORY_END_DATE,
    "endday": _CATEGORY_END_DATE,
    "endtime": _CATEGORY_END_TIME,
    "finishtime": _CATEGORY_END_TIME,
    "stoptime": _CATEGORY_END_TIME,
}

_DATETIME_PATTERNS = (
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %I:%M %p",
    "%m/%d/%Y %I:%M:%S %p",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %I:%M %p",
    "%Y/%m/%d %H:%M",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%dT%H:%M:%S",
)

_DATE_PATTERNS = (
    "%m/%d/%Y",
    "%m/%d/%y",
    "%Y-%m-%d",
    "%Y/%m/%d",
)

_TIME_PATTERNS = (
    "%H:%M",
    "%H:%M:%S",
    "%H",
    "%I:%M %p",
    "%I:%M:%S %p",
    "%I %p",
    "%I%p",
    "%I:%M%p",
)


@dataclass
class NormalizedRow:
    event_name: str
    casino: str
    location: str
    offer: str
    start: datetime
    end: datetime
    warnings: list[str]


@dataclass
class NormalizationResult:
    input_path: Path
    output_path: Path
    rows_read: int
    rows_written: int
    skipped_rows: int
    warnings: list[str]


def normalize_csv(
    input_path: Path,
    output_path: Path | None = None,
    *,
    sort_rows: bool = True,
    overwrite: bool = True,
) -> NormalizationResult:
    """Normalise a CSV file and write it in the format expected by the app."""

    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path
    else:
        output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    if output_path.exists() and not overwrite and output_path != input_path:
        raise FileExistsError(f"Refusing to overwrite existing file: {output_path}")

    logger.info("Normalising CSV %s -> %s", input_path, output_path)

    with input_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise ValueError(f"{input_path}: missing header row")

        categories = _categorise_headers(reader.fieldnames)
        rows: list[NormalizedRow] = []
        warnings: list[str] = []
        rows_read = 0
        skipped_rows = 0

        for row_number, row in enumerate(reader, start=2):
            rows_read += 1
            if not _row_has_data(row.values()):
                skipped_rows += 1
                continue

            normalized = _normalise_row(row, categories, row_number)
            rows.append(normalized)
            warnings.extend(normalized.warnings)

    if sort_rows:
        rows.sort(
            key=lambda r: (
                r.start,
                r.end,
                r.casino.lower(),
                r.event_name.lower(),
            )
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=EXPECTED_COLUMNS, lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "EventName": row.event_name,
                    "Casino": row.casino,
                    "Location": row.location,
                    "Offer": row.offer,
                    "StartDate": _format_datetime(row.start),
                    "EndDate": _format_datetime(row.end),
                }
            )

    return NormalizationResult(
        input_path=input_path,
        output_path=output_path,
        rows_read=rows_read,
        rows_written=len(rows),
        skipped_rows=skipped_rows,
        warnings=warnings,
    )


def find_candidate_csv_paths(include_modified: bool = True) -> list[Path]:
    """Return CSV paths detected from git status output."""

    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        logger.debug("git executable not available; skipping CSV auto-detect")
        return []

    if proc.returncode != 0:
        logger.debug("git status returned %s; stdout=%s", proc.returncode, proc.stdout)
        return []

    candidates: list[Path] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue

        status = line[:2]
        path_fragment = line[3:].strip()
        if "->" in path_fragment:
            path_fragment = path_fragment.split("->", 1)[1].strip()

        if not path_fragment.lower().endswith(".csv"):
            continue

        if status == "??" or status.startswith("A"):
            candidates.append(Path(path_fragment))
        elif include_modified and status.strip().startswith("M"):
            candidates.append(Path(path_fragment))

    return candidates


def _normalise_row(
    row: dict[str, str],
    categories: dict[str, list[str]],
    row_number: int,
) -> NormalizedRow:
    warnings: list[str] = []

    event_name = _first_value(row, categories.get(_CATEGORY_EVENT, ()))
    if not event_name:
        raise ValueError(f"Row {row_number}: missing event name")

    casino = _first_value(row, categories.get(_CATEGORY_CASINO, ()))
    if not casino:
        raise ValueError(f"Row {row_number}: missing casino name")

    location_segments = _collect_values(row, categories.get(_CATEGORY_LOCATION_PRIMARY, ()))
    location_parts = _collect_values(row, categories.get(_CATEGORY_LOCATION_PART, ()))
    location = _combine_segments(location_segments, ", ")
    if location_parts:
        combined_parts = _combine_segments(location_parts, ", ")
        if combined_parts:
            location = _combine_location(location, combined_parts)

    offer_primary = _collect_values(row, categories.get(_CATEGORY_OFFER, ()))
    offer_extra = _collect_values(row, categories.get(_CATEGORY_OFFER_EXTRA, ()))
    offer = _combine_segments(offer_primary, " | ")
    extra_text = _combine_segments(offer_extra, " | ")
    if extra_text:
        offer = f"{offer} - {extra_text}" if offer else extra_text

    start_dt, start_warning = _resolve_datetime(
        datetime_values=_collect_values(row, categories.get(_CATEGORY_START_DATETIME, ())),
        date_values=_collect_values(row, categories.get(_CATEGORY_START_DATE, ())),
        time_values=_collect_values(row, categories.get(_CATEGORY_START_TIME, ())),
        fallback=time(0, 0),
        label="StartDate",
        row_number=row_number,
    )
    if start_warning:
        warnings.append(start_warning)

    end_dt, end_warning = _resolve_datetime(
        datetime_values=_collect_values(row, categories.get(_CATEGORY_END_DATETIME, ())),
        date_values=_collect_values(row, categories.get(_CATEGORY_END_DATE, ())),
        time_values=_collect_values(row, categories.get(_CATEGORY_END_TIME, ())),
        fallback=time(23, 59),
        label="EndDate",
        row_number=row_number,
        minimum=start_dt,
    )
    if end_warning:
        warnings.append(end_warning)

    return NormalizedRow(
        event_name=event_name,
        casino=casino,
        location=location,
        offer=offer,
        start=start_dt,
        end=end_dt,
        warnings=warnings,
    )


def _resolve_datetime(
    *,
    datetime_values: Sequence[str],
    date_values: Sequence[str],
    time_values: Sequence[str],
    fallback: time,
    label: str,
    row_number: int,
    minimum: datetime | None = None,
) -> tuple[datetime, str | None]:
    for value in datetime_values:
        parsed = _parse_datetime(value)
        if parsed:
            if minimum and parsed < minimum:
                return minimum, (
                    f"Row {row_number}: {label} earlier than start; "
                    "clamping to start time"
                )
            return parsed, None

    parsed_date = None
    chosen_date_value = None
    for value in date_values:
        parsed_date = _parse_date(value)
        if parsed_date:
            chosen_date_value = value
            break

    if not parsed_date:
        raise ValueError(f"Row {row_number}: missing {label} date value")

    parsed_time = None
    for value in time_values:
        parsed_time = _parse_time(value)
        if parsed_time is not None:
            break

    if parsed_time is None and chosen_date_value:
        dt_candidate = _parse_datetime(chosen_date_value)
        if dt_candidate:
            parsed_time = dt_candidate.time()

    warning = None
    if parsed_time is None:
        parsed_time = fallback
        warning = (
            f"Row {row_number}: missing {label} time; defaulting to "
            f"{fallback.hour}:{fallback.minute:02d}"
        )

    combined = datetime.combine(parsed_date, parsed_time)
    if minimum and combined < minimum:
        warning = (
            f"Row {row_number}: {label} earlier than start; clamping to start time"
        )
        combined = minimum

    return combined, warning


def _collect_values(row: dict[str, str], headers: Iterable[str]) -> list[str]:
    values: list[str] = []
    for header in headers:
        value = row.get(header)
        if value is None:
            continue

        text = _normalise_whitespace(str(value))
        if text and text not in values:
            values.append(text)
    return values


def _first_value(row: dict[str, str], headers: Iterable[str]) -> str:
    for header in headers:
        value = row.get(header)
        if value is None:
            continue
        text = _normalise_whitespace(str(value))
        if text:
            return text
    return ""


def _combine_segments(segments: Sequence[str], delimiter: str) -> str:
    filtered = [segment for segment in segments if segment]
    if not filtered:
        return ""
    return delimiter.join(filtered)


def _combine_location(primary: str, parts: str) -> str:
    if primary and parts:
        if parts in primary:
            return primary
        if primary in parts:
            return parts
        return f"{primary}, {parts}"
    return primary or parts


def _parse_datetime(value: str) -> datetime | None:
    text = _normalise_whitespace(value)
    if not text:
        return None

    if text.endswith("Z"):
        text = text[:-1]

    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is not None:
            parsed = parsed.replace(tzinfo=None)
        return parsed
    except ValueError:
        pass

    excel = _parse_excel_serial(text)
    if excel:
        return excel

    for pattern in _DATETIME_PATTERNS:
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue
    return None


def _parse_date(value: str) -> date | None:
    text = _normalise_whitespace(value)
    if not text:
        return None

    if text.endswith("Z"):
        text = text[:-1]

    dt_candidate = _parse_datetime(text)
    if dt_candidate:
        return dt_candidate.date()

    try:
        parsed = datetime.fromisoformat(text)
        return parsed.date()
    except ValueError:
        pass

    excel = _parse_excel_serial(text)
    if excel:
        return excel.date()

    for pattern in _DATE_PATTERNS:
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue

    return None


def _parse_time(value: str) -> time | None:
    text = _normalise_whitespace(value)
    if not text:
        return None

    upper = text.upper().replace("A.M.", "AM").replace("P.M.", "PM")

    if re.fullmatch(r"\d{3}", upper):
        hours = int(upper[0])
        minutes = int(upper[1:])
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            return time(hours, minutes)
    if re.fullmatch(r"\d{4}", upper):
        hours = int(upper[:2])
        minutes = int(upper[2:])
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            return time(hours, minutes)

    for pattern in _TIME_PATTERNS:
        try:
            return datetime.strptime(upper, pattern).time()
        except ValueError:
            continue

    return None


def _parse_excel_serial(value: str) -> datetime | None:
    try:
        as_float = float(value)
    except ValueError:
        return None

    if as_float <= 0:
        return None

    days = timedelta(days=as_float)
    return _EXCEL_EPOCH + days


def _normalise_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _row_has_data(values: Iterable[str | None]) -> bool:
    for value in values:
        if value and _normalise_whitespace(str(value)):
            return True
    return False


def _format_datetime(value: datetime) -> str:
    return f"{value.month}/{value.day}/{value.year} {value.hour}:{value.minute:02d}"


def _categorise_headers(headers: Sequence[str]) -> dict[str, list[str]]:
    categories: dict[str, list[str]] = {}

    for header in headers:
        token = _normalise_header_token(header)
        category = _HEADER_CATEGORY_MAP.get(token)
        if not category:
            continue
        categories.setdefault(category, []).append(header)

    return categories


def _normalise_header_token(header: str) -> str:
    return re.sub(r"[^a-z0-9]", "", header.lower())
