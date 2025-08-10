from pathlib import Path

import pandas as pd
import pytest
from app_components.data import categorize_offer_type_updated, load_event_data


@pytest.mark.parametrize(
    "event_name,offer,expected",
    [
        ("Car Giveaway", "", "Giveaway"),
        ("", "free play bonus", "Free-Play"),
        ("Points Multiplier", "", "Point-Based"),
        ("Hotel Stay", "", "Hospitality-Rewards"),
        ("Tournament", "", "Special-Events"),
        ("Generic Promo", "", "Offer"),
    ],
)
def test_categorize_offer_type_updated_basic(event_name, offer, expected):
    assert categorize_offer_type_updated(event_name, offer) == expected


def test_categorize_offer_type_handles_missing():
    assert categorize_offer_type_updated(None, None) == "Offer"


@pytest.mark.usefixtures("casino")
def test_load_event_data_localizes_dates(tmp_path: Path, casino):
    csv_path = tmp_path / "sample.csv"
    df = pd.DataFrame(
        {
            "EventName": ["Test Event"],
            "Casino": [casino],
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


@pytest.mark.usefixtures("casino")
def test_load_event_data_handles_dst(tmp_path: Path, casino):
    csv_path = tmp_path / "dst.csv"
    df = pd.DataFrame(
        {
            "EventName": ["DST Event"],
            "Casino": [casino],
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


@pytest.mark.usefixtures("casino")
def test_load_event_data_handles_dst_fall(tmp_path: Path, casino):
    csv_path = tmp_path / "dst_fall.csv"
    df = pd.DataFrame(
        {
            "EventName": ["DST Fall"],
            "Casino": [casino],
            "Location": ["Test"],
            "Offer": [""],
            "StartDate": ["11/2/2025 0:30"],
            "EndDate": ["11/2/2025 2:30"],
        }
    )
    df.to_csv(csv_path, index=False)

    result = load_event_data(csv_path)

    delta = result.loc[0, "EndDate"] - result.loc[0, "StartDate"]
    assert delta.total_seconds() == 10800
