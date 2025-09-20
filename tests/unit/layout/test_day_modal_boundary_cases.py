#!/usr/bin/env python3
"""
Test script to verify day modal logic includes all boundary cases.
"""
from datetime import datetime, timedelta

import pandas as pd
from casino_calendar.dash_app.visualization.charts import generate_day_view_html
from casino_calendar.dash_app.services.layout_state import to_naive_utc
from casino_calendar.services.colors import get_color


def test_day_modal_boundary_cases():
    """Test day modal logic with events that start/end on the selected day."""

    # Create test data with events that start and end on specific days
    clicked_date = to_naive_utc(datetime(2025, 8, 5))  # Test date

    # IMPORTANT: Test data times need to be in naive UTC format (as stored in CSV)
    # To create times that will show as PDT local times, we need to add 7 hours
    # For example: to get 10 AM PDT, we store 17:00 UTC (10 + 7)

    # Event that starts on the day but ends the next day
    event_starts_today = {
        "EventName": "Starts Today",
        "Casino": "ilani",
        "Location": "",
        "OfferType": "",  # Added missing OfferType column
        "Offer": "Test offer starts today",
        "StartDate": clicked_date.replace(hour=17),  # 10 AM PDT (17:00 UTC)
        "EndDate": clicked_date.replace(hour=19)
        + timedelta(days=1),  # 12 PM PDT tomorrow
    }

    # Event that starts yesterday but ends today
    event_ends_today = {
        "EventName": "Ends Today",
        "Casino": "ilani",
        "Location": "",
        "OfferType": "",  # Added missing OfferType column
        "Offer": "Test offer ends today",
        "StartDate": clicked_date.replace(hour=15)
        - timedelta(days=1),  # 8 AM PDT yesterday
        "EndDate": clicked_date.replace(hour=23),  # 4 PM PDT today
    }

    # Event that is entirely within the day
    event_same_day = {
        "EventName": "Same Day",
        "Casino": "ilani",
        "Location": "",
        "OfferType": "",  # Added missing OfferType column
        "Offer": "Test offer same day",
        "StartDate": clicked_date.replace(hour=16),  # 9 AM PDT today (16:00 UTC)
        "EndDate": clicked_date.replace(hour=0)
        + timedelta(days=1),  # 5 PM PDT today (00:00 UTC next day)
    }

    # Event that starts exactly at day boundary (midnight PDT)
    event_starts_midnight = {
        "EventName": "Starts Midnight",
        "Casino": "ilani",
        "Location": "",
        "OfferType": "",  # Added missing OfferType column
        "Offer": "Test offer starts midnight",
        "StartDate": clicked_date.replace(hour=7),  # Midnight PDT (07:00 UTC)
        "EndDate": clicked_date.replace(hour=13),  # 6 AM PDT today
    }

    # Event that ends exactly at day boundary (midnight PDT)
    event_ends_midnight = {
        "EventName": "Ends Midnight",
        "Casino": "ilani",
        "Location": "",
        "OfferType": "",  # Added missing OfferType column
        "Offer": "Test offer ends midnight",
        "StartDate": clicked_date.replace(hour=1)
        - timedelta(days=1),  # 6 PM PDT yesterday
        "EndDate": clicked_date.replace(hour=7),  # Midnight PDT today (07:00 UTC)
    }

    test_events = pd.DataFrame(
        [
            event_starts_today,
            event_ends_today,
            event_same_day,
            event_starts_midnight,
            event_ends_midnight,  # Added the missing midnight event
        ]
    )

    result = generate_day_view_html(test_events, clicked_date, get_color, 1024)

    # Check that we generated the expected elements
    assert len(result) >= 2, "Should generate header and grid elements"

    grid = result[1]

    # Check that we have the grid with event blocks
    assert hasattr(grid, "children"), "Grid should have children"

    event_blocks = [
        child
        for child in grid.children
        if hasattr(child, "className")
        and child.className
        and "event-block-day" in child.className
    ]

    # All 5 boundary case events should be included in the day modal
    assert len(event_blocks) == 5, f"Expected 5 events, got {len(event_blocks)}"

    # Verify we have the expected event titles
    event_titles = [getattr(block, "title", "") for block in event_blocks]
    expected_events = [
        "Starts Today",
        "Ends Today",
        "Same Day",
        "Starts Midnight",
        "Ends Midnight",
    ]

    for expected_event in expected_events:
        assert expected_event in event_titles, f"Missing event: {expected_event}"


def test_day_modal_midnight_boundary_edge_case():
    """Test specific edge case where event ends exactly at midnight (day boundary)."""

    clicked_date = to_naive_utc(datetime(2025, 8, 5))

    # Event that ends exactly at midnight (start of the clicked day)
    # This event SHOULD be included because EndDate >= day_start includes the boundary
    test_events = pd.DataFrame(
        [
            {
                "EventName": "Ends At Midnight",
                "Casino": "ilani",
                "Location": "",
                "OfferType": "",  # Added missing OfferType column
                "Offer": "Event ends exactly at day boundary",
                "StartDate": clicked_date.replace(hour=1)
                - timedelta(days=1),  # 6 PM PDT yesterday
                "EndDate": clicked_date.replace(
                    hour=7
                ),  # Midnight PDT today (07:00 UTC)
            }
        ]
    )

    result = generate_day_view_html(test_events, clicked_date, get_color, 1024)

    assert len(result) >= 2, "Should generate header and grid elements"
    grid = result[1]

    event_blocks = [
        child
        for child in grid.children
        if hasattr(child, "className")
        and child.className
        and "event-block-day" in child.className
    ]

    # Event ending exactly at midnight SHOULD be included
    # boundary is inclusive with >= operator
    assert len(event_blocks) == 1, (
        "Event ending exactly at midnight should be included with >= boundary, "
        f"got {len(event_blocks)} events"
    )


def test_day_modal_midnight_boundary_inclusive_case():
    """Test edge case where event ends just after midnight (should be included)."""

    clicked_date = to_naive_utc(datetime(2025, 8, 5))

    # Event that ends just after midnight (should be included)
    test_events = pd.DataFrame(
        [
            {
                "EventName": "Ends After Midnight",
                "Casino": "ilani",
                "Location": "",
                "OfferType": "",
                "Offer": "Event ends just after day boundary",
                "StartDate": clicked_date.replace(hour=1)
                - timedelta(days=1),  # 6 PM PDT yesterday
                "EndDate": clicked_date.replace(hour=7, minute=1),  # 00:01 AM PDT today
            }
        ]
    )

    result = generate_day_view_html(test_events, clicked_date, get_color, 1024)

    assert len(result) >= 2, "Should generate header and grid elements"
    grid = result[1]

    event_blocks = [
        child
        for child in grid.children
        if hasattr(child, "className")
        and child.className
        and "event-block-day" in child.className
    ]

    # Event ending 1 minute into the day should be included
    assert len(event_blocks) == 1, (
        "Event ending just after midnight should be included, "
        f"got {len(event_blocks)} events"
    )
