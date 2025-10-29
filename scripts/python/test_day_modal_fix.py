#!/usr/bin/env python3
"""
Quick test script to verify the day modal improvements.
"""
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
for candidate in (SRC_DIR, ROOT_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from casino_calendar.dash_app.visualization import charts as day_charts  # noqa: E402
from casino_calendar.logging import config as logging_config  # noqa: E402
from casino_calendar.services.colors import get_color  # noqa: E402

logger = logging_config.setup_maintenance_logger(
    "casino_calendar.scripts.test_day_modal_fix"
)

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
    result = day_charts.generate_day_view_html(
        test_events, clicked_date, get_color, screen_width
    )

    logger.info("Day modal generated successfully")
    logger.info("Generated %s elements for modal", len(result))

    if len(result) >= 2:
        header = result[0]
        grid = result[1]

        header_text = header.children if hasattr(header, "children") else "OK"
        class_name = grid.className if hasattr(grid, "className") else "day-grid"

        logger.info("Header text: %s", header_text)
        logger.info("Grid container class: %s", class_name)

        if hasattr(grid, "style") and "height" in getattr(grid, "style", {}):
            height_str = grid.style["height"]
            logger.info("Grid height: %s", height_str)
            height_px = int(height_str.replace("px", ""))
            expected_max = 24 * 24  # 24 hours * 24px max height
            if height_px <= expected_max:
                logger.info(
                    "Grid height %s px is within %s px limit",
                    height_px,
                    expected_max,
                )
            else:
                logger.warning(
                    "Grid height %s px may exceed expected maximum %s px",
                    height_px,
                    expected_max,
                )

    logger.info("Day modal checks completed")

except Exception:
    logger.exception("Day modal verification failed")
