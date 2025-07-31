#!/usr/bin/env python3
"""Test the updated day modal filtering logic."""

import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from app_components.utils import to_pdt, to_naive_utc


def test_august_1st_filtering():
    """Test filtering for August 1st day modal."""

    # Create test events with various date ranges
    test_events = pd.DataFrame(
        [
            {
                "EventName": "July 28 - Aug 3 (Should NOT appear)",
                "Casino": "Test Casino",
                "StartDate": "2025-07-28 10:00",
                "EndDate": "2025-08-03 14:00",
                "Offer": "Too long event",
                "OfferType": "Free Play",
            },
            {
                "EventName": "July 31 - Aug 1 (Should appear)",
                "Casino": "Test Casino",
                "StartDate": "2025-07-31 18:00",  # Previous day
                "EndDate": "2025-08-01 12:00",  # Current day
                "Offer": "Previous day event",
                "OfferType": "Dining",
            },
            {
                "EventName": "Aug 1 only (Should appear)",
                "Casino": "Test Casino",
                "StartDate": "2025-08-01 09:00",  # Current day
                "EndDate": "2025-08-01 17:00",  # Current day
                "Offer": "Same day event",
                "OfferType": "Slot Play",
            },
            {
                "EventName": "Aug 1 - Aug 2 (Should appear)",
                "Casino": "Test Casino",
                "StartDate": "2025-08-01 20:00",  # Current day
                "EndDate": "2025-08-02 10:00",  # Next day
                "Offer": "Next day event",
                "OfferType": "Free Play",
            },
            {
                "EventName": "July 30 - Aug 1 (Should NOT appear)",
                "Casino": "Test Casino",
                "StartDate": "2025-07-30 15:00",  # Too early (2 days before)
                "EndDate": "2025-08-01 15:00",  # Current day
                "Offer": "Starts too early",
                "OfferType": "Dining",
            },
        ]
    )

    # Convert dates
    test_events["StartDate"] = pd.to_datetime(test_events["StartDate"])
    test_events["EndDate"] = pd.to_datetime(test_events["EndDate"])

    # Test August 1st day modal
    aug_1_naive = datetime(2025, 8, 1)
    aug_1_date = to_naive_utc(aug_1_naive)  # Simulate callback

    print(f"Testing August 1st day modal...")
    print(f"User clicked: {aug_1_naive}")
    print(f"Callback date: {aug_1_date}")

    # Apply the new filtering logic
    from pytz import timezone

    PDT = timezone("America/Los_Angeles")

    if aug_1_date.tzinfo is None:
        day_start = PDT.localize(
            aug_1_date.replace(hour=0, minute=0, second=0, microsecond=0)
        )
    else:
        day_start = to_pdt(aug_1_date).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    day_end = day_start + timedelta(days=1)

    print(f"Day start: {day_start}")
    print(f"Day end: {day_end}")

    events = test_events.copy()
    events["StartDate"] = pd.to_datetime(events["StartDate"]).map(to_pdt)
    events["EndDate"] = pd.to_datetime(events["EndDate"]).map(to_pdt)

    # Calculate day boundaries
    prev_day_start = day_start - timedelta(days=1)
    next_day_end = day_end + timedelta(days=1)

    print(f"Previous day start: {prev_day_start}")
    print(f"Next day end: {next_day_end}")

    print("\nAll events:")
    for idx, row in events.iterrows():
        print(f"  {row['EventName']}: {row['StartDate']} to {row['EndDate']}")

    # Apply new filter
    filtered_events = events[
        (events["StartDate"] >= prev_day_start)
        & (events["StartDate"] < next_day_end)
        & (events["EndDate"] > prev_day_start)
        & (events["EndDate"] <= next_day_end)
    ]

    print(f"\nFiltered events for August 1st ({len(filtered_events)} events):")
    for idx, row in filtered_events.iterrows():
        print(f"  ✅ {row['EventName']}: {row['StartDate']} to {row['EndDate']}")

        # Check each condition
        start_after_prev = row["StartDate"] >= prev_day_start
        start_before_next_end = row["StartDate"] < next_day_end
        end_after_prev = row["EndDate"] > prev_day_start
        end_before_next_end = row["EndDate"] <= next_day_end

        print(f"     Start >= prev day: {start_after_prev}")
        print(f"     Start < next day end: {start_before_next_end}")
        print(f"     End > prev day: {end_after_prev}")
        print(f"     End <= next day end: {end_before_next_end}")

    expected_events = [
        "July 31 - Aug 1 (Should appear)",
        "Aug 1 only (Should appear)",
        "Aug 1 - Aug 2 (Should appear)",
    ]

    actual_events = filtered_events["EventName"].tolist()

    print(f"\nExpected: {expected_events}")
    print(f"Actual: {actual_events}")

    if set(expected_events) == set(actual_events):
        print("✅ Day modal filtering is working correctly!")
    else:
        print("❌ Day modal filtering has issues!")
        print(f"Missing: {set(expected_events) - set(actual_events)}")
        print(f"Extra: {set(actual_events) - set(expected_events)}")


if __name__ == "__main__":
    test_august_1st_filtering()
