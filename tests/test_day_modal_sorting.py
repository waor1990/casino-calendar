#!/usr/bin/env python3
"""
Test the sorting logic for event blocks in the day modal.
"""

from datetime import datetime

import pandas as pd

from app_components.plotting import generate_day_view_html
from utils.colors import get_color


def test_day_modal_sorting():
    """Test that event blocks are sorted by start time, casino, then category."""

    # Create test data with events that should be sorted
    clicked_date = datetime(2025, 8, 6, 0, 0, 0)  # naive UTC

    test_events = pd.DataFrame(
        [
            {
                "EventName": "Late Event",
                "Casino": "Casino B",
                "OfferType": "Giveaway",
                "Offer": "Late event",
                "StartDate": pd.Timestamp("2025-08-06 18:00:00"),  # 6 PM
                "EndDate": pd.Timestamp("2025-08-06 20:00:00"),
            },
            {
                "EventName": "Early Event Z Casino",
                "Casino": "Casino Z",
                "OfferType": "Free-Play",
                "Offer": "Early event Z",
                "StartDate": pd.Timestamp("2025-08-06 10:00:00"),  # 10 AM
                "EndDate": pd.Timestamp("2025-08-06 12:00:00"),
            },
            {
                "EventName": "Early Event A Casino",
                "Casino": "Casino A",
                "OfferType": "Point-Based",
                "Offer": "Early event A",
                "StartDate": pd.Timestamp("2025-08-06 10:00:00"),  # 10 AM (same time)
                "EndDate": pd.Timestamp("2025-08-06 12:00:00"),
            },
            {
                "EventName": "Same Casino Different Category 1",
                "Casino": "Casino A",
                "OfferType": "Free-Play",
                # Should come before Point-Based alphabetically
                "Offer": "Same casino category 1",
                "StartDate": pd.Timestamp("2025-08-06 14:00:00"),  # 2 PM
                "EndDate": pd.Timestamp("2025-08-06 16:00:00"),
            },
            {
                "EventName": "Same Casino Different Category 2",
                "Casino": "Casino A",
                "OfferType": "Point-Based",  # Should come after Free-Play
                "Offer": "Same casino category 2",
                "StartDate": pd.Timestamp("2025-08-06 14:00:00"),  # 2 PM (same time)
                "EndDate": pd.Timestamp("2025-08-06 16:00:00"),
            },
        ]
    )

    # Generate the day view
    result = generate_day_view_html(test_events, clicked_date, get_color, 1024)

    # Extract the grid container
    assert len(result) >= 2, "Should have header and grid elements"
    grid = result[1]

    # Find all event blocks
    assert hasattr(grid, "children") and grid.children, "Grid should have children"
    event_blocks = [
        child
        for child in grid.children
        if hasattr(child, "className")
        and child.className
        and "event-block-day" in child.className
    ]

    assert len(event_blocks) == 5, f"Expected 5 event blocks, got {len(event_blocks)}"

    # Extract event titles to verify sorting order
    event_titles = [block.title for block in event_blocks]

    # Expected order:
    # 1. 10 AM: Casino A (Point-Based) - "Early Event A Casino"
    # 2. 10 AM: Casino Z (Free-Play) - "Early Event Z Casino"
    # 3. 2 PM: Casino A (Free-Play) - "Same Casino Different Category 1"
    # 4. 2 PM: Casino A (Point-Based) - "Same Casino Different Category 2"
    # 5. 6 PM: Casino B (Giveaway) - "Late Event"
    expected_order = [
        "Early Event A Casino",  # 10 AM, Casino A, Point-Based
        "Early Event Z Casino",  # 10 AM, Casino Z, Free-Play
        "Same Casino Different Category 1",  # 2 PM, Casino A, Free-Play
        "Same Casino Different Category 2",  # 2 PM, Casino A, Point-Based
        "Late Event",  # 6 PM, Casino B, Giveaway
    ]

    print("Actual order:", event_titles)
    print("Expected order:", expected_order)

    assert (
        event_titles == expected_order
    ), f"Event order mismatch!\nActual: {event_titles}\nExpected: {expected_order}"

    print("✅ Day modal sorting test passed!")


if __name__ == "__main__":
    test_day_modal_sorting()
