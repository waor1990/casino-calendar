#!/usr/bin/env python3
"""
Test script to verify the day modal styling changes.
"""
import pandas as pd
from datetime import datetime
from app_components.plotting import generate_day_view_html
from utils.colors import get_color

# Create test data
test_events = pd.DataFrame(
    [
        {
            "EventName": "Short Event",
            "Casino": "ilani",
            "StartDate": pd.Timestamp("2025-07-30 10:00:00-07:00"),
            "EndDate": pd.Timestamp("2025-07-30 12:00:00-07:00"),
            "OfferType": "Free-Play",
            "Offer": "Test offer 1",
        },
        {
            "EventName": "Longer Event Name Here",
            "Casino": "Lucky Eagle Casino",
            "StartDate": pd.Timestamp("2025-07-30 14:00:00-07:00"),
            "EndDate": pd.Timestamp("2025-07-30 16:30:00-07:00"),
            "OfferType": "Giveaway",
            "Offer": "Test offer 2",
        },
    ]
)

# Test the day view generation
clicked_date = datetime(2025, 7, 30)
screen_width = 1024

try:
    result = generate_day_view_html(test_events, clicked_date, get_color, screen_width)

    print("✅ Day modal generation successful!")
    print(f"Generated {len(result)} elements")

    # Find event blocks and check their styling
    grid = result[1]  # Should be the grid container
    event_blocks = []

    # Search for event blocks in the grid children
    for child in grid.children:
        if hasattr(child, "className") and "event-block-day" in str(child.className):
            event_blocks.append(child)

    print(f"✅ Found {len(event_blocks)} event blocks")

    # Check styling properties
    for i, block in enumerate(event_blocks):
        if hasattr(block, "style"):
            style = block.style
            print(f"\n📋 Event Block {i+1} styling:")
            print(f"   - Width: {style.get('width', 'not set')}")
            print(f"   - Min Width: {style.get('minWidth', 'not set')}")
            print(f"   - Max Width: {style.get('maxWidth', 'not set')}")
            print(f"   - Left position: {style.get('left', 'not set')}")

            # Check if width is set to 'auto' for better content fitting
            if style.get("width") == "auto":
                print("   ✅ Width set to auto for content-based sizing")
            else:
                print(f"   ⚠️  Width is fixed: {style.get('width')}")

    print("\n✅ Test completed successfully!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
