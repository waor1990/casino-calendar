"""CSV loader utilities for Casino Calendar event data."""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from casino_calendar.logging.config import setup_logger
from casino_calendar.settings import DATA_DIR

from .transforms import categorize_offer_types, to_naive_utc

logger = setup_logger(__name__)

DEFAULT_CSV_PATH = DATA_DIR / "raw" / "casino_events.csv"


def load_event_data(csv_path: str | Path | None = None) -> pd.DataFrame:
    """Load event data with timestamps normalized to naive UTC."""

    path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH
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

    sort_columns = [col for col in ["StartDate", "EndDate", "Casino", "EventName"] if col in df.columns]
    if sort_columns:
        df = df.sort_values(sort_columns).reset_index(drop=True)

    load_time = time.time() - start_time
    logger.info("Processed event data in %.3f seconds", load_time)
    return df
