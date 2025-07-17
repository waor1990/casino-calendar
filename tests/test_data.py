from pathlib import Path

import pandas as pd

from app_components.data import categorize_offer_type_updated, load_event_data


def test_categorize_offer_type_updated_basic():
    assert categorize_offer_type_updated("Car Giveaway", "") == "Giveaway"
    assert categorize_offer_type_updated("", "free play bonus") == "Free-Play"
    assert categorize_offer_type_updated("Points Multiplier", "") == "Point-Based"
    assert categorize_offer_type_updated("Hotel Stay", "") == "Hospitality-Rewards"
    assert categorize_offer_type_updated("Tournament", "") == "Special-Events"
    assert categorize_offer_type_updated("Generic Promo", "") == "Offer"


def test_categorize_offer_type_handles_missing():
    assert categorize_offer_type_updated(None, None) == "Offer"


def test_load_event_data_localizes_dates(tmp_path: Path):
    csv_path = tmp_path / "sample.csv"
    df = pd.DataFrame(
        {
            "EventName": ["Test Event"],
            "Casino": ["Test Casino"],
            "Location": ["Test"],
            "Offer": ["free play"],
            "StartDate": ["1/1/2025 10:00"],
            "EndDate": ["1/1/2025 12:00"],
        }
    )
    df.to_csv(csv_path, index=False)

    result = load_event_data(csv_path)

    assert result["StartDate"].dt.tz is None
    assert result.loc[0, "OfferType"] == "Free-Play"


def test_load_event_data_handles_dst(tmp_path: Path):
    csv_path = tmp_path / "dst.csv"
    df = pd.DataFrame(
        {
            "EventName": ["DST Event"],
            "Casino": ["Test Casino"],
            "Location": ["Test"],
            "Offer": [""],
            "StartDate": ["3/9/2025 1:30"],
            "EndDate": ["3/9/2025 3:30"],
        }
    )
    df.to_csv(csv_path, index=False)

    result = load_event_data(csv_path)

    delta = result.loc[0, "EndDate"] - result.loc[0, "StartDate"]
    assert delta.total_seconds() == 3600
