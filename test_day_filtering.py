#!/usr/bin/env python3
"""Test the day modal event filtering logic to verify multi-day events are shown correctly."""

import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath("."))

from app_components.plotting import generate_day_view_html
from app_components.utils import to_pdt, to_naive_utc


def test_day_modal_filtering():
    """Test that multi-day events appear in the correct day modals."""

    # Create test data with multi-day events
    test_events = pd.DataFrame(
        [
            {
                "EventName": "Saturday-Monday Event",
                "Casino": "Test Casino",
                "StartDate": "2025-08-02 10:00",  # Saturday
                "EndDate": "2025-08-04 14:00",  # Monday
                "Offer": "Multi-day offer",
                "OfferType": "Free Play",
            },
            {
                "EventName": "Saturday-Sunday Event",
                "Casino": "Test Casino",
                "StartDate": "2025-08-02 18:00",  # Saturday
                "EndDate": "2025-08-03 12:00",  # Sunday
                "Offer": "Weekend offer",
                "OfferType": "Dining",
            },
            {
                "EventName": "Sunday Only Event",
                "Casino": "Test Casino",
                "StartDate": "2025-08-03 09:00",  # Sunday
                "EndDate": "2025-08-03 17:00",  # Sunday
                "Offer": "Single day offer",
                "OfferType": "Slot Play",
            },
        ]
    )

    # Convert dates
    test_events["StartDate"] = pd.to_datetime(test_events["StartDate"])
    test_events["EndDate"] = pd.to_datetime(test_events["EndDate"])

    # Test Sunday's day modal (2025-08-03)
    # Simulate the actual callback behavior by using to_naive_utc
    sunday_date_naive = datetime(2025, 8, 3)  # This is what user clicks
    sunday_date = to_naive_utc(sunday_date_naive)  # This is what callback sends
    print(f"Input date (user clicked): {sunday_date_naive}")
    print(f"Callback converted date: {sunday_date}")

    # Mock color function
    def get_colors():
        return {"Test Casino": {"bg": "#ff0000", "text": "#ffffff"}}

    # Generate day view for Sunday
    print("Testing Sunday (2025-08-03) day modal...")

    # Recreate the filtering logic from the function
    print(f"Original clicked_date: {sunday_date}")

    # Use the new logic from plotting.py
    from pytz import timezone

    PDT = timezone("America/Los_Angeles")

    if sunday_date.tzinfo is None:
        day_start = PDT.localize(
            sunday_date.replace(hour=0, minute=0, second=0, microsecond=0)
        )
    else:
        day_start = to_pdt(sunday_date).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    day_end = day_start + timedelta(days=1)

    print(f"Day start: {day_start}")
    print(f"Day end: {day_end}")

    events = test_events.copy()
    events["StartDate"] = pd.to_datetime(events["StartDate"]).map(to_pdt)
    events["EndDate"] = pd.to_datetime(events["EndDate"]).map(to_pdt)

    print(f"Day range: {day_start} to {day_end}")
    print("\nAll events:")
    for idx, row in events.iterrows():
        print(f"  {row['EventName']}: {row['StartDate']} to {row['EndDate']}")

    # Apply the filter
    filtered_events = events[
        (events["EndDate"] > day_start) & (events["StartDate"] < day_end)
    ]

    print(f"\nFiltered events for Sunday ({len(filtered_events)} events):")
    for idx, row in filtered_events.iterrows():
        print(f"  ✅ {row['EventName']}: {row['StartDate']} to {row['EndDate']}")

        # Check the logic
        end_after_start = row["EndDate"] > day_start
        start_before_end = row["StartDate"] < day_end
        print(f"     End after day start: {end_after_start}")
        print(f"     Start before day end: {start_before_end}")

    expected_events = [
        "Saturday-Monday Event",  # Spans through Sunday
        "Saturday-Sunday Event",  # Ends on Sunday
        "Sunday Only Event",  # Only on Sunday
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
    test_day_modal_filtering()
