#!/usr/bin/env python3
"""Simple test to debug day modal filtering."""

from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app_components.utils import to_pdt

# Test the date conversion issue
sunday_date = datetime(2025, 8, 3)  # August 3rd, 2025 (Sunday)
print(f"Input date: {sunday_date}")

pdt_date = to_pdt(sunday_date)
print(f"PDT converted: {pdt_date}")

day_start = pdt_date.replace(hour=0, minute=0, second=0, microsecond=0)
day_end = day_start + timedelta(days=1)

print(f"Day start: {day_start}")
print(f"Day end: {day_end}")

# Test event times
event_start = to_pdt(datetime(2025, 8, 3, 9, 0))  # Sunday 9 AM
event_end = to_pdt(datetime(2025, 8, 3, 17, 0))  # Sunday 5 PM

print(f"\nSunday event: {event_start} to {event_end}")

# Test the filter condition
end_after_start = event_end > day_start
start_before_end = event_start < day_end

print(f"Event end > day start: {event_end} > {day_start} = {end_after_start}")
print(f"Event start < day end: {event_start} < {day_end} = {start_before_end}")
print(f"Should be included: {end_after_start and start_before_end}")
