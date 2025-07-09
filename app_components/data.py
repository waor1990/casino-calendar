import pandas as pd

from .utils import PDT


def categorize_offer_type_updated(event_name, offer):
    event_name = str(event_name).lower() if pd.notna(event_name) else ""
    offer = str(offer).lower() if pd.notna(offer) else ""

    # Define keywords for each category
    giveaway_keywords = [
        "giveaway",
        "giveaways",
        "gift",
        "gifts",
        "redeem",
        "earbuds",
        "headphones",
        "luggage",
        "necklace",
        "bracelet",
        "earrings",
        "tool set",
        "barbuds",
        "t-shirt",
        "wearable",
        "cooler",
        "backpack",
        "camping set",
        "cookware",
        "outdoor stove",
        "fan",
        "fishing pole",
        "bathroom set",
        "john wayne",
        "frigidaire",
        "collection",
        "cash",
        "drawing",
        "sweepstakes",
        "hot seat",
        "prize",
        "scratcher",
        "bonus drawing",
        "win it",
        "winnings",
        "fortune wheel",
        "money",
        "bonanza",
        "red white drawings",
        "hourly",
    ]
    free_play_cash_drawing_keywords = [
        "free play",
        "slot play",
        "free-play",
        "promo play",
        "lucky bucks",
        "mystery bonus",
        "vault of riches",
        "kiosk game",
        "freeplay",
        "xtra rewards",
    ]
    multiplier_points_keywords = [
        "multiplier",
        "points",
        "x points",
        "status points",
        "points multiplier",
        "point multiplier",
    ]
    hotel_travel_dining_shopping_keywords = [
        "hotel",
        "stay",
        "rv",
        "cruise",
        "dining",
        "shopping",
        "buffet",
        "food",
        "restaurant",
        "meal",
        "discount",
        "merchandise",
        "spa",
        "travel",
        "trip",
        "room night",
        "standard room",
        "double rewards",
        "% off",
    ]
    special_event_keywords = [
        "tournament",
        "event",
        "brunch",
        "reception",
        "fiesta",
        "party",
        "taco crawl",
        "special",
        "celebration",
        "invite",
        "parade",
        "festival",
        "show",
        "game",
        "bingo",
        "concert",
        "birthday",
    ]
    vehicle_car_giveaway_keywords = [
        "car",
        "toyota",
        "tundra",
        "volkswagen",
        "jetta",
        "kia k5",
        "dodge charger",
        "rv",
        "atv",
        "truck",
        "land cruiser",
    ]

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


def load_event_data(csv_path="data/casino_events.csv"):
    df = pd.read_csv(csv_path)

    for col in ["StartDate", "EndDate"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        if df[col].dt.tz is None:
            df[col] = df[col].dt.tz_localize(PDT)
        else:
            df[col] = df[col].dt.tz_convert(PDT)

    df["OfferType"] = df.apply(
        lambda row: categorize_offer_type_updated(
            row.get("EventName"), row.get("Offer")
        ),
        axis=1,
    )

    return df
