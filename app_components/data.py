import re

import pandas as pd

from .utils import PDT


def categorize_offer_type(offer_text: str) -> str:
    """Return a normalized offer category for ``offer_text``."""

    if not isinstance(offer_text, str):
        return "Unknown"

    text = offer_text.lower()

    free_play_keywords = [
        "free play",
        "freeplay",
        "promo play",
        "slot credit",
        "slot play",
        "bonus play",
    ]
    if any(keyword in text for keyword in free_play_keywords):
        return "Free-Play"

    drawing_keywords = [
        "hot seat",
        "drawing",
        "cash giveaway",
        "swipe & win",
        "swipe and win",
    ]
    if any(keyword in text for keyword in drawing_keywords):
        return "Drawings"

    if re.search(r"\b\d+x\s*points\b", text) or "multiplier" in text:
        return "Point-Based"
    if "tier credit" in text or "earn & get" in text or "earn and get" in text:
        return "Point-Based"
    if re.search(r"earn.*\d+.*points", text):
        return "Point-Based"

    giveaway_keywords = [
        "gift giveaway",
        "pickup",
        "hotel stay",
        "hotel room",
        "dining credit",
        "gas card",
        "voucher",
    ]
    if any(keyword in text for keyword in giveaway_keywords):
        return "Giveaways"

    return "Unknown"


def load_event_data(csv_path="casino_events.csv"):
    df = pd.read_csv(csv_path)

    for col in ["StartDate", "EndDate"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        if df[col].dt.tz is None:
            df[col] = df[col].dt.tz_localize(PDT)
        else:
            df[col] = df[col].dt.tz_convert(PDT)

    df["OfferType"] = df["Offer"].apply(categorize_offer_type)

    return df
