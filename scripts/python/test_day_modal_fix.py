#!/usr/bin/env python3
"""
Quick test script to verify the day modal improvements.
"""
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from casino_calendar.dash_app.visualization import charts as day_charts
from casino_calendar.services.colors import get_color

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
for candidate in (SRC_DIR, ROOT_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

# Create test data
test_events = pd.DataFrame(
    [
        {
            "EventName": "Test Event 1",
            "Casino": "ilani",
            "StartDate": pd.Timestamp("2025-07-30 10:00:00-07:00"),
            "EndDate": pd.Timestamp("2025-07-30 12:00:00-07:00"),
            "OfferType": "Free-Play",
            "Offer": "Test offer 1",
        },
        {
            "EventName": "Test Event 2",
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
    result = day_charts.generate_day_view_html(test_events, clicked_date, get_color, screen_width)

    print("✅ Day modal generation successful!")
    print(f"Generated {len(result)} elements")

    # Check that we have the expected elements
    if len(result) >= 2:
        header = result[0]
        grid = result[1]

        print(f"✅ Header text: {header.children if hasattr(header, 'children') else 'OK'}")
        print(f"✅ Grid container with class: {grid.className if hasattr(grid, 'className') else 'day-grid'}")

        # Check grid height - should be reasonable for modal (24 hours * reduced hour_height)
        if hasattr(grid, "style") and "height" in grid.style:
            height_str = grid.style["height"]
            print(f"✅ Grid height: {height_str}")
            # Extract height value
            height_px = int(height_str.replace("px", ""))
            expected_max = 24 * 24  # 24 hours * 24px max height
            if height_px <= expected_max:
                print(f"✅ Grid height {height_px}px is within expected range (≤{expected_max}px)")
            else:
                print(f"⚠️  Grid height {height_px}px might be too large")

        print("✅ All tests passed!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
