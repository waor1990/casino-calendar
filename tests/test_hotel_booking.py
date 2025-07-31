#!/usr/bin/env python3
"""Test hotel booking data loading."""

import json

# Test that the hotel booking data loads correctly
try:
    with open("data/hotel_book_sites.json", "r") as f:
        data = json.load(f)
    print("Hotel booking sites loaded successfully!")
    print(f"Total casinos with booking info: {len(data)}")
    print("Sample entries:")
    for i, (casino, url) in enumerate(data.items()):
        if i < 3:
            print(
                f"  {casino}: {url[:50]}..." if len(url) > 50 else f"  {casino}: {url}"
            )
    print("\nCasinos with N/A booking:")
    na_count = sum(1 for url in data.values() if url == "N/A")
    print(f"  Count: {na_count}")

    # Show some casinos that do have booking URLs
    print("\nCasinos with active booking URLs:")
    active_count = 0
    for casino, url in data.items():
        if url != "N/A" and active_count < 3:
            print(
                f"  {casino}: {url[:50]}..." if len(url) > 50 else f"  {casino}: {url}"
            )
            active_count += 1

    print(f"\nTotal active booking URLs: {len(data) - na_count}")

except Exception as e:
    print(f"Error loading hotel booking data: {e}")
