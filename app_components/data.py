import json
import time
from datetime import timedelta
from pathlib import Path

import pandas as pd
from pytz import UTC, AmbiguousTimeError, NonExistentTimeError

from .logging_config import setup_logger
from .utils import PDT

# Initialize module logger
logger = setup_logger(__name__)


def categorize_offer_type_updated(event_name: str | None, offer: str | None) -> str:
    """Return an offer type based on keywords found in ``event_name`` or ``offer``."""
    logger.debug(f"Categorizing offer type for event: {event_name}, offer: {offer}")

    event_name = str(event_name).lower() if pd.notna(event_name) else ""
    offer = str(offer).lower() if pd.notna(offer) else ""

    # Load keywords from JSON
    DATA_DIR = Path(__file__).resolve().parent.parent / "data"
    keywords_file = DATA_DIR / "offer_keywords.json"

    try:
        with open(keywords_file, encoding="utf-8") as f:
            keywords = json.load(f)
        logger.debug(f"Loaded offer keywords from {keywords_file}")
    except FileNotFoundError:
        logger.error(f"Keywords file not found: {keywords_file}")
        return "Offer"
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in keywords file: {e}", exc_info=True)
        return "Offer"

    giveaway_keywords = keywords["giveaway_keywords"]
    free_play_cash_drawing_keywords = keywords["free_play_cash_drawing_keywords"]
    multiplier_points_keywords = keywords["multiplier_points_keywords"]
    hotel_travel_dining_shopping_keywords = keywords[
        "hotel_travel_dining_shopping_keywords"
    ]
    special_event_keywords = keywords["special_event_keywords"]
    vehicle_car_giveaway_keywords = keywords["vehicle_car_giveaway_keywords"]

    # Check for categories in a specific order of precedence
    if any(keyword in event_name for keyword in vehicle_car_giveaway_keywords) or any(
        keyword in offer for keyword in vehicle_car_giveaway_keywords
    ):
        category = "Giveaway"
        logger.debug(f"Categorized as {category} (vehicle/car keywords)")
        return category
    elif any(keyword in event_name for keyword in giveaway_keywords) or any(
        keyword in offer for keyword in giveaway_keywords
    ):
        category = "Giveaway"
        logger.debug(f"Categorized as {category} (giveaway keywords)")
        return category
    elif any(
        keyword in event_name for keyword in free_play_cash_drawing_keywords
    ) or any(keyword in offer for keyword in free_play_cash_drawing_keywords):
        category = "Free-Play"
        logger.debug(f"Categorized as {category} (free-play keywords)")
        return category
    elif any(keyword in event_name for keyword in multiplier_points_keywords) or any(
        keyword in offer for keyword in multiplier_points_keywords
    ):
        category = "Point-Based"
        logger.debug(f"Categorized as {category} (points keywords)")
        return category
    elif any(
        keyword in event_name for keyword in hotel_travel_dining_shopping_keywords
    ) or any(keyword in offer for keyword in hotel_travel_dining_shopping_keywords):
        category = "Hospitality-Rewards"
        logger.debug(f"Categorized as {category} (hospitality keywords)")
        return category
    elif any(keyword in event_name for keyword in special_event_keywords) or any(
        keyword in offer for keyword in special_event_keywords
    ):
        category = "Special-Events"
        logger.debug(f"Categorized as {category} (special event keywords)")
        return category

    logger.debug("No keywords matched, defaulting to 'Offer'")
    return "Offer"


def load_event_data(csv_path: str = "data/casino_events.csv") -> pd.DataFrame:
    """Load event data from ``csv_path`` with times stored as naive UTC."""
    logger.info(f"Loading event data from {csv_path}")
    start_time = time.time()

    try:
        df = pd.read_csv(csv_path)
        logger.info(
            f"Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns"
        )
        logger.debug(f"CSV columns: {list(df.columns)}")
    except FileNotFoundError:
        logger.error(f"Event data file not found: {csv_path}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"Event data file is empty: {csv_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load event data: {e}", exc_info=True)
        raise

    def _to_naive_utc(ts: pd.Timestamp) -> pd.Timestamp:
        """Return ``ts`` converted to naive UTC handling DST edges."""
        if pd.isna(ts):
            return ts
        if ts.tzinfo is None:
            try:
                localized = PDT.localize(ts, is_dst=None)
                logger.debug(f"Successfully localized timestamp: {ts}")
            except AmbiguousTimeError:
                localized = PDT.localize(ts, is_dst=False)
                logger.warning(f"Ambiguous time encountered, using DST=False: {ts}")
            except NonExistentTimeError:
                localized = PDT.localize(ts + timedelta(hours=1))
                logger.warning(f"Non-existent time encountered, adding 1 hour: {ts}")
        else:
            localized = ts.astimezone(PDT)
        dt = localized.astimezone(UTC).replace(tzinfo=None)
        return pd.Timestamp(dt)

    logger.debug("Converting date columns to naive UTC")
    for col in ["StartDate", "EndDate"]:
        if col in df.columns:
            logger.debug(f"Processing {col} column")
            df[col] = pd.to_datetime(df[col], errors="coerce")

            # Count invalid dates
            invalid_dates = df[col].isna().sum()
            if invalid_dates > 0:
                logger.warning(f"{invalid_dates} invalid dates found in {col} column")

            df[col] = df[col].map(_to_naive_utc)
        else:
            logger.warning(f"Expected column '{col}' not found in data")

    logger.debug("Categorizing offer types...")
    try:
        df["OfferType"] = df.apply(
            lambda row: categorize_offer_type_updated(
                row.get("EventName"), row.get("Offer")
            ),
            axis=1,
        )

        # Log offer type distribution
        offer_counts = df["OfferType"].value_counts()
        logger.info(f"Offer type distribution: {offer_counts.to_dict()}")

    except Exception as e:
        logger.error(f"Failed to categorize offer types: {e}", exc_info=True)
        raise

    load_time = time.time() - start_time
    logger.info(f"Event data processing completed in {load_time:.3f}s")

    return df
