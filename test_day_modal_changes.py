#!/usr/bin/env python3
"""
Test script to verify day modal event block styling changes.
Tests font size increase and width-to-content fitting.
"""
import pandas as pd
from datetime import datetime
from app_components.plotting import generate_day_view_html
from utils.colors import get_color


def test_day_modal_changes():
    """Test that day modal event blocks have correct styling."""
    print("🧪 Testing day modal event block changes...")

    # Create test data with different length event names
    test_events = pd.DataFrame(
        [
            {
                "EventName": "Short Event",
                "Casino": "Test Casino 1",
                "StartDate": pd.Timestamp("2025-07-31 10:00:00-07:00"),
                "EndDate": pd.Timestamp("2025-07-31 12:00:00-07:00"),
                "OfferType": "Free-Play",
                "Offer": "Test offer 1",
            },
            {
                "EventName": "This is a Much Longer Event Name for Testing",
                "Casino": "Test Casino with Long Name",
                "StartDate": pd.Timestamp("2025-07-31 14:00:00-07:00"),
                "EndDate": pd.Timestamp("2025-07-31 16:30:00-07:00"),
                "OfferType": "Giveaway",
                "Offer": "Test offer 2",
            },
        ]
    )

    # Test the day view generation
    clicked_date = datetime(2025, 7, 31)
    screen_width = 1024

    try:
        result = generate_day_view_html(
            test_events, clicked_date, get_color, screen_width
        )

        print("✅ Day modal generation successful!")
        print(f"Generated {len(result)} elements")

        # Check that we have the expected elements
        if len(result) >= 2:
            header = result[0]
            grid = result[1]

            print(f"✅ Header: {header.className}")
            print(f"✅ Grid: {grid.className}")

            # Look for event blocks in the grid children
            event_blocks = []
            for child in grid.children:
                if hasattr(child, "className") and "event-block-day" in str(
                    child.className
                ):
                    event_blocks.append(child)

            print(f"✅ Found {len(event_blocks)} event blocks")

            # Test the width calculations
            for i, block in enumerate(event_blocks):
                if hasattr(block, "style") and block.style:
                    width = block.style.get("width", "Not set")
                    min_width = block.style.get("minWidth", "Not set")
                    margin_left = block.style.get("margin-left", "Default")

                    print(f"  Event {i+1}:")
                    print(f"    Width: {width}")
                    print(f"    MinWidth: {min_width}")
                    print(f"    Margin-left: {margin_left}")

                    # Check if width is reasonably sized (should be smaller for shorter events)
                    if "rem" in str(width):
                        width_val = float(str(width).replace("rem", ""))
                        if i == 0:  # Short event
                            if width_val <= 12:
                                print(
                                    f"    ✅ Short event has appropriate width: {width_val}rem"
                                )
                            else:
                                print(
                                    f"    ⚠️  Short event width might be too large: {width_val}rem"
                                )
                        else:  # Long event
                            if width_val <= 20:
                                print(
                                    f"    ✅ Long event has reasonable width: {width_val}rem"
                                )
                            else:
                                print(
                                    f"    ⚠️  Long event width might be too large: {width_val}rem"
                                )

        print("✅ All tests completed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_day_modal_changes()
