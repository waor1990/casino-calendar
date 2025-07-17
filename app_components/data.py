import json
from datetime import timedelta
from pathlib import Path

import pandas as pd
from pytz import UTC, AmbiguousTimeError, NonExistentTimeError

from .utils import PDT


def categorize_offer_type_updated(event_name: str | None, offer: str | None) -> str:
    """Return an offer type based on keywords found in ``event_name`` or ``offer``."""

    event_name = str(event_name).lower() if pd.notna(event_name) else ""
    offer = str(offer).lower() if pd.notna(offer) else ""

    # Load keywords from JSON
    DATA_DIR = Path(__file__).resolve().parent.parent / "data"
    with open(DATA_DIR / "offer_keywords.json", encoding="utf-8") as f:
        keywords = json.load(f)

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
        return "Giveaway"
    elif any(keyword in event_name for keyword in giveaway_keywords) or any(
        keyword in offer for keyword in giveaway_keywords
    ):
        return "Giveaway"
    elif any(
        keyword in event_name for keyword in free_play_cash_drawing_keywords
    ) or any(keyword in offer for keyword in free_play_cash_drawing_keywords):
        return "Free-Play"
    elif any(keyword in event_name for keyword in multiplier_points_keywords) or any(
        keyword in offer for keyword in multiplier_points_keywords
    ):
        return "Point-Based"
    elif any(
        keyword in event_name for keyword in hotel_travel_dining_shopping_keywords
    ) or any(keyword in offer for keyword in hotel_travel_dining_shopping_keywords):
        return "Hospitality-Rewards"
    elif any(keyword in event_name for keyword in special_event_keywords) or any(
        keyword in offer for keyword in special_event_keywords
    ):
        return "Special-Events"
    return "Offer"


def load_event_data(csv_path: str = "data/casino_events.csv") -> pd.DataFrame:
    """Load event data from ``csv_path`` with times stored as naive UTC."""
    df = pd.read_csv(csv_path)

    def _to_naive_utc(ts: pd.Timestamp) -> pd.Timestamp:
        """Return ``ts`` converted to naive UTC handling DST edges."""
        if pd.isna(ts):
            return ts
        if ts.tzinfo is None:
            try:
                localized = PDT.localize(ts, is_dst=None)
            except AmbiguousTimeError:
                localized = PDT.localize(ts, is_dst=False)
            except NonExistentTimeError:
                localized = PDT.localize(ts + timedelta(hours=1))
        else:
            localized = ts.astimezone(PDT)
        dt = localized.astimezone(UTC).replace(tzinfo=None)
        return pd.Timestamp(dt)

    for col in ["StartDate", "EndDate"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        df[col] = df[col].map(_to_naive_utc)

    df["OfferType"] = df.apply(
        lambda row: categorize_offer_type_updated(
            row.get("EventName"), row.get("Offer")
        ),
        axis=1,
    )

    return df
