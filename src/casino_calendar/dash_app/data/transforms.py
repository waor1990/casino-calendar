"""Data transformation helpers for Casino Calendar events."""

from __future__ import annotations

import re
from datetime import timedelta

import pandas as pd
from casino_calendar.logging.config import setup_logger
from casino_calendar.services.config_cache import get_config
from casino_calendar.settings import APP_TIMEZONE, UTC_TZ
from pytz import AmbiguousTimeError, NonExistentTimeError

logger = setup_logger(__name__)


def _build_keyword_pattern(keys: list[str]) -> str:
    """Return a regex pattern matching keywords with whole-word boundaries."""

    whole_words: list[str] = []
    phrases: list[str] = []
    for key in keys:
        if re.fullmatch(r"[A-Za-z0-9]+", key):
            whole_words.append(rf"(?<!\w){re.escape(key)}(?!\w)")
        else:
            phrases.append(re.escape(key))
    return "|".join(whole_words + phrases)


def categorize_offer_type(event_name: str | None, offer: str | None) -> str:
    """Return an offer type based on keywords found in event_name or offer."""

    event_name = str(event_name).lower() if pd.notna(event_name) else ""
    offer = str(offer).lower() if pd.notna(offer) else ""

    keywords = get_config("lookups/offer_keywords.json")
    if not keywords:
        logger.error("Could not load offer keywords configuration")
        return "Offer"

    giveaway_keywords = keywords["giveaway_keywords"]
    free_play_cash_drawing_keywords = keywords["free_play_cash_drawing_keywords"]
    multiplier_points_keywords = keywords["multiplier_points_keywords"]
    hotel_travel_dining_shopping_keywords = keywords[
        "hotel_travel_dining_shopping_keywords"
    ]
    special_event_keywords = keywords["special_event_keywords"]
    vehicle_car_giveaway_keywords = keywords["vehicle_car_giveaway_keywords"]

    patterns = {
        "vehicle": re.compile(_build_keyword_pattern(vehicle_car_giveaway_keywords)),
        "giveaway": re.compile(_build_keyword_pattern(giveaway_keywords)),
        "free_play": re.compile(
            _build_keyword_pattern(free_play_cash_drawing_keywords)
        ),
        "multiplier": re.compile(_build_keyword_pattern(multiplier_points_keywords)),
        "hospitality": re.compile(
            _build_keyword_pattern(hotel_travel_dining_shopping_keywords)
        ),
        "special": re.compile(_build_keyword_pattern(special_event_keywords)),
    }

    # Check for categories in a specific order of precedence
    if patterns["vehicle"].search(event_name) or patterns["vehicle"].search(offer):
        return "Giveaway"
    if patterns["giveaway"].search(event_name) or patterns["giveaway"].search(offer):
        return "Giveaway"
    if patterns["free_play"].search(event_name) or patterns["free_play"].search(offer):
        return "Free-Play"
    if patterns["multiplier"].search(event_name) or patterns["multiplier"].search(
        offer
    ):
        return "Point-Based"
    if patterns["hospitality"].search(event_name) or patterns["hospitality"].search(
        offer
    ):
        return "Hospitality-Rewards"
    if patterns["special"].search(event_name) or patterns["special"].search(offer):
        return "Special-Events"

    return "Offer"


def categorize_offer_types(df: pd.DataFrame) -> pd.Series:
    """Vectorized offer type categorization for an entire DataFrame."""
    logger.debug("Categorizing offer types using vectorized operations")

    keywords = get_config("lookups/offer_keywords.json")
    if not keywords:
        logger.error("Could not load offer keywords configuration")
        return pd.Series("Offer", index=df.index)

    event_name = (
        df.get("EventName", pd.Series(index=df.index, dtype=str)).fillna("").str.lower()
    )
    offer = df.get("Offer", pd.Series(index=df.index, dtype=str)).fillna("").str.lower()

    category = pd.Series("Offer", index=df.index)

    def match(keys: list[str]) -> pd.Series:
        pattern = _build_keyword_pattern(keys)
        return event_name.str.contains(pattern, regex=True) | offer.str.contains(
            pattern, regex=True
        )

    masks = {
        "vehicle": match(keywords["vehicle_car_giveaway_keywords"]),
        "giveaway": match(keywords["giveaway_keywords"]),
        "free_play": match(keywords["free_play_cash_drawing_keywords"]),
        "multiplier": match(keywords["multiplier_points_keywords"]),
        "hospitality": match(keywords["hotel_travel_dining_shopping_keywords"]),
        "special": match(keywords["special_event_keywords"]),
    }

    category[masks["vehicle"]] = "Giveaway"
    category[masks["giveaway"] & ~masks["vehicle"]] = "Giveaway"
    used = masks["vehicle"] | masks["giveaway"]
    category[masks["free_play"] & ~used] = "Free-Play"
    used |= masks["free_play"]
    category[masks["multiplier"] & ~used] = "Point-Based"
    used |= masks["multiplier"]
    category[masks["hospitality"] & ~used] = "Hospitality-Rewards"
    used |= masks["hospitality"]
    category[masks["special"] & ~used] = "Special-Events"

    return category


def to_naive_utc(timestamp: pd.Timestamp) -> pd.Timestamp:
    """Return timestamp converted to naive UTC handling DST edges."""

    if pd.isna(timestamp):
        return timestamp

    if timestamp.tzinfo is None:
        try:
            localized = APP_TIMEZONE.localize(timestamp, is_dst=None)
            logger.debug("Successfully localized timestamp %s", timestamp)
        except AmbiguousTimeError:
            localized = APP_TIMEZONE.localize(timestamp, is_dst=False)
            logger.warning(
                "Ambiguous time encountered for %s; using DST=False", timestamp
            )
        except NonExistentTimeError:
            localized = APP_TIMEZONE.localize(timestamp + timedelta(hours=1))
            logger.warning(
                "Non-existent time encountered for %s; adding 1 hour", timestamp
            )
    else:
        localized = timestamp.astimezone(APP_TIMEZONE)

    dt = localized.astimezone(UTC_TZ).replace(tzinfo=None)
    return pd.Timestamp(dt)
