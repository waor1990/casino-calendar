"""CSV loader utilities for Casino Calendar event data."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

import pandas as pd

from casino_calendar.logging.config import setup_logger
from casino_calendar.settings import DATA_DIR

from .transforms import categorize_offer_types, to_naive_utc

logger = setup_logger(__name__)

DEFAULT_CSV_PATH = DATA_DIR / "raw" / "casino_events.csv"
EDITED_SUFFIX = ".edited"


def _edited_copy_path(base_path: Path) -> Path:
    """Return the path used for persisted edits next to ``base_path``."""

    return base_path.with_name(f"{base_path.stem}{EDITED_SUFFIX}{base_path.suffix}")


def resolve_active_csv_path(csv_path: str | Path | None = None) -> Path:
    """Return the CSV path to load, preferring a newer edited copy if present."""

    base_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH
    edited_path = _edited_copy_path(base_path)

    if edited_path.exists():
        try:
            edited_mtime = edited_path.stat().st_mtime
        except OSError:
            logger.debug("Unable to read edited file metadata", exc_info=True)
        else:
            try:
                base_mtime = base_path.stat().st_mtime
            except OSError:
                logger.info("Using edited events file at %s", edited_path)
                return edited_path

            if edited_mtime >= base_mtime:
                logger.info("Using edited events file at %s", edited_path)
                return edited_path

    return base_path


def _write_dataframe_atomic(df: pd.DataFrame, target_path: Path) -> None:
    """Persist ``df`` to ``target_path`` using an atomic replace."""

    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_name(f".{target_path.name}.tmp")
    df.to_csv(temp_path, index=False)
    temp_path.replace(target_path)


def save_event_data(
    events: pd.DataFrame | Iterable[dict], csv_path: str | Path | None = None
) -> Path:
    """Persist ``events`` to disk and return the path that was written."""

    base_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH
    edited_path = _edited_copy_path(base_path)

    if not isinstance(events, pd.DataFrame):
        events = pd.DataFrame(events)

    drop_columns = [col for col in ["_row_index"] if col in events.columns]
    if drop_columns:
        events = events.drop(columns=drop_columns)

    for column in ["StartDate", "EndDate"]:
        if column in events.columns:
            events[column] = pd.to_datetime(events[column], errors="coerce")

    try:
        logger.info("Saving event data to %s", base_path)
        _write_dataframe_atomic(events, base_path)
    except OSError as exc:
        logger.warning(
            "Unable to write events to %s: %s. Falling back to edited copy.",
            base_path,
            exc,
        )
        edited_path.parent.mkdir(parents=True, exist_ok=True)
        _write_dataframe_atomic(events, edited_path)
        return edited_path

    try:
        if edited_path.exists():
            edited_path.unlink()
    except OSError:
        logger.debug("Unable to remove edited events file", exc_info=True)

    return base_path


def load_event_data(csv_path: str | Path | None = None) -> pd.DataFrame:
    """Load event data with timestamps normalized to naive UTC."""

    path = resolve_active_csv_path(csv_path)
    logger.info("Loading event data from %s", path)
    start_time = time.time()

    try:
        df = pd.read_csv(path)
        logger.info(
            "Successfully loaded CSV with %d rows and %d columns",
            len(df),
            len(df.columns),
        )
        logger.debug("CSV columns: %s", ", ".join(map(str, df.columns)))
    except FileNotFoundError:
        logger.error("Event data file not found: %s", path)
        raise
    except pd.errors.EmptyDataError:
        logger.error("Event data file is empty: %s", path)
        raise
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to load event data: %s", exc, exc_info=True)
        raise

    logger.debug("Converting date columns to naive UTC")
    for column in ["StartDate", "EndDate"]:
        if column not in df.columns:
            logger.warning("Expected column '%s' not found in data", column)
            continue

        logger.debug("Processing %s column", column)
        df[column] = pd.to_datetime(df[column], errors="coerce")

        invalid_dates = df[column].isna().sum()
        if invalid_dates:
            logger.warning("%d invalid dates found in %s column", invalid_dates, column)

        df[column] = df[column].map(to_naive_utc)

    logger.debug("Categorizing offer types")
    df["OfferType"] = categorize_offer_types(df)
    offer_counts = df["OfferType"].value_counts()
    logger.info("Offer type distribution: %s", offer_counts.to_dict())

    load_time = time.time() - start_time
    logger.info("Processed event data in %.3f seconds", load_time)
    return df
