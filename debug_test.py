#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.getcwd())

from datetime import datetime
import pandas as pd
from app_components.plotting import generate_day_view_html
from utils.colors import get_color
from app_components.utils import to_naive_utc

# Recreate the test data
clicked = to_naive_utc(datetime(2025, 8, 5))
df = pd.DataFrame(
    {
        "EventName": [
            "Very Long Event Name One",
            "Another Extremely Long Event Name",
        ],
        "Casino": ["ilani", "ilani"],
        "OfferType": ["", ""],
        "Offer": ["", ""],
        "StartDate": [
            clicked.replace(hour=9),
            clicked.replace(hour=12),
        ],
        "EndDate": [
            clicked.replace(hour=10),
            clicked.replace(hour=13),
        ],
    }
)

print("Test data:")
print(df)
print()

# Generate the day view
result = generate_day_view_html(df, clicked, get_color, 1024)
print(f"Generated {len(result)} elements")

# Look at the grid children
grid_children = result[1].children
event_divs = [
    c
    for c in grid_children
    if getattr(c, "className", "") and "event-block-day" in c.className
]

print(f"Found {len(event_divs)} event divs")

# Check each event div
for i, (div, name) in enumerate(zip(event_divs, df["EventName"])):
    print(f"\nEvent {i+1}: {name}")
    print(f"  className: {getattr(div, 'className', 'N/A')}")
    print(f"  style: {getattr(div, 'style', 'N/A')}")
    expected_width = f"{len(name) + 2}ch"
    actual_minwidth = div.style.get("minWidth") if hasattr(div, "style") else None
    print(f"  Expected minWidth: {expected_width}")
    print(f"  Actual minWidth: {actual_minwidth}")
    print(f"  Test result: {'PASS' if actual_minwidth == expected_width else 'FAIL'}")
