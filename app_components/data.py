import re

import pandas as pd

from .utils import PDT


def categorize_offer_type(offer_text: str, event_name: str = "") -> str:
    """Return a normalized offer category for ``offer_text`` or ``event_name``."""

    if not isinstance(offer_text, str) and not isinstance(event_name, str):
        return "Offer"

    text = f"{offer_text} {event_name}".lower()

    free_play_keywords = [
        "free play",
        "freeplay",
        "promo play",
        "slot credit",
        "slot play",
        "bonus play",
        "bucks",
    ]
    if any(keyword in text for keyword in free_play_keywords):
        return "Free-Play"

    drawing_keywords = [
        "hot seat",
        "drawing",
        "cash giveaway",
        "every half hour",
        "swipe & win",
        "spin and win",
        "swipe and win",
    ]
    if any(keyword in text for keyword in drawing_keywords):
        return "Drawings"
    
    number_or_word_pattern = (
        r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten"
        r"eleven|twelve|thirteen|fourteen|fifteen|sixteen"
        r"seventeen|eighteen|nineteen|twenty)"
    )

    if re.search(
        rf"\bevery\s+{number_or_word_pattern}\s+\w+", text
    ):  # Looks for patterns like 'every 2 hours' or 'every two hours'
        return "Drawings"
    if re.search(
        rf"\b{number_or_word_pattern}\s+cash\b", text
    ):  # Looks for patterns like '50 cash' or 'fifty cash'
        return "Drawings"
    if re.search(
        rf"\b{number_or_word_pattern}\s+prize\b", text
    ):  # Looks for patterns like '1st prize' or 'first prize'
        return "Drawings"
    if re.search(
        rf"\b{number_or_word_pattern}\s+winners\b", text
    ):  # Looks for patterns like '3 winners' or 'three winners'
        return "Drawings"

    if ( 
        re.search(rf"\b\d+x(?:\s+\w+){0,2}\s*points\b", text) or "multiplier" in text
    ):  # Looks for patterns like '2x points' or checks for 'multiplier'
        return "Point-Based"
    if (
        "tier credit" in text or "earn & get" in text or "earn and get" in text
    ):  # Checks for specific phrases related to points
        return "Point-Based"
    if (
        re.search(r"earn.*\d+.*points", text)
    ):  # Looks for patterns where points are mentioned in the context of earning
        return "Point-Based"

    giveaway_keywords = [
        "gift giveaway",
        "gift",
        "item",
        "pickup",
        "hotel stay",
        "rv stay",
        "hotel room",
        "hotel offer",
        "dining credit",
        "gas card",
        "gas giveaway",
        "voucher",
        "free for",
    ]
    if any(keyword in text for keyword in giveaway_keywords):
        return "Giveaways"

    return "Offer"


def load_event_data(csv_path="casino_events.csv"):
    df = pd.read_csv(csv_path)

    for col in ["StartDate", "EndDate"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        if df[col].dt.tz is None:
            df[col] = df[col].dt.tz_localize(PDT)
        else:
            df[col] = df[col].dt.tz_convert(PDT)

    df["OfferType"] = df.apply(
        lambda row: categorize_offer_type(row.get("Offer"), row.get("EventName")),
        axis=1,
    )

    return df
