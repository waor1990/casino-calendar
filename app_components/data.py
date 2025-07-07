import re

import pandas as pd

from .utils import PDT

def categorize_offer_type_updated(event_name, offer):
    event_name = str(event_name).lower() if pd.notna(event_name) else ''
    offer = str(offer).lower() if pd.notna(offer) else ''

    # Define keywords for each category
    giveaway_keywords = ['giveaway', 'gift', 'redeem', 'earbuds', 'headphones', 'luggage', 'necklace', 'bracelet', 'earrings', 'tool set', 'barbuds', 't-shirt', 'wearable', 'cooler', 'backpack', 'camping set', 'cookware', 'outdoor stove', 'fan', 'fishing pole', 'bathroom set', 'john wayne', 'frigidaire', 'countertop collection']
    free_play_cash_drawing_keywords = ['free play', 'slot play', 'free-play', 'cash', 'drawing', 'sweepstakes', 'jackpot', 'hot seat', 'prize', 'spin', 'scratcher', 'promo play', 'lucky bucks', 'wild flowers', 'bonus drawing', 'mystery bonus', 'swipe', 'win it', 'vault of riches', 'lucky flowers', 'big cash', 'bingo', 'kiosk game', 'winnings', 'fortune wheel', 'money', 'bonanza', 'piñata', 'red white drawings', 'freeplay']
    multiplier_points_keywords = ['multiplier', 'points', 'x points', 'status points', 'rewards dollars', 'bonus entries']
    hotel_travel_dining_shopping_keywords = ['hotel', 'stay', 'rv', 'cruise', 'dining', 'shopping', 'buffet', 'food', 'restaurant', 'meal', 'discount', 'merchandise', 'spa', 'travel', 'trip', 'room night', 'standard room', '% off']
    special_event_keywords = ['tournament', 'event', 'brunch', 'reception', 'fiesta', 'party', 'taco crawl', 'special', 'celebration', 'invite', 'parade', 'festival', 'show', 'game', 'bingo', 'concert', 'birthday']
    vehicle_car_giveaway_keywords = ['car', 'toyota', 'tundra', 'volkswagen', 'jetta', 'kia k5', 'dodge charger', 'rv', 'atv', 'truck', 'land cruiser']

    # Check for categories in a specific order of precedence
    if any(keyword in event_name for keyword in vehicle_car_giveaway_keywords) or \
       any(keyword in offer for keyword in vehicle_car_giveaway_keywords):
        return 'Giveaway'
    elif any(keyword in event_name for keyword in giveaway_keywords) or \
         any(keyword in offer for keyword in giveaway_keywords):
        return 'Giveaway'
    elif any(keyword in event_name for keyword in free_play_cash_drawing_keywords) or \
         any(keyword in offer for keyword in free_play_cash_drawing_keywords):
        return 'Free-Play'
    elif any(keyword in event_name for keyword in multiplier_points_keywords) or \
         any(keyword in offer for keyword in multiplier_points_keywords):
        return 'Point-Based'
    elif any(keyword in event_name for keyword in hotel_travel_dining_shopping_keywords) or \
         any(keyword in offer for keyword in hotel_travel_dining_shopping_keywords):
        return 'Hospitality-Rewards'
    elif any(keyword in event_name for keyword in special_event_keywords) or \
         any(keyword in offer for keyword in special_event_keywords):
        return 'Special-Events'
    return 'Offer'

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
        re.search(r"\b\d+x(?:\s+\w+){0,2}\s*points\b", text) or "multiplier" in text
    ):  # Looks for patterns like '2x points' or checks for 'multiplier'
        return "Point-Based"
    if (
        "tier credit" in text or "earn & get" in text or "earn and get" in text
    ):  # Checks for specific phrases related to points
        return "Point-Based"
    if re.search(
        r"earn.*\d+.*points", text
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
