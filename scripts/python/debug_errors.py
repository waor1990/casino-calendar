#!/usr/bin/env python3
"""
Error Debugging Guide for Casino Calendar Application

This script demonstrates how to trigger and view detailed error information
in the show_event_modal callback and other parts of the application.
"""

import sys
from pathlib import Path

# Ensure project modules are importable when executed directly
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
for candidate in (SRC_DIR, PROJECT_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from casino_calendar.logging import config as logging_config  # noqa: E402

logger = logging_config.setup_maintenance_logger("casino_calendar.scripts.debug_errors")


def demonstrate_error_logging():
    """Demonstrate how exc_info=True provides full tracebacks."""

    logger.info("=== Error Logging Demonstration ===")

    # Simulate an error without exc_info (old way)
    try:
        _ = 10 / 0  # noqa: B018 - deliberate exception for demonstration
    except Exception as exc:
        logger.info("1. Old error logging (without exc_info):")
        logger.error("Error in demo callback: %s", exc)

    # Simulate an error with exc_info (new way)
    try:
        _ = 10 / 0  # noqa: B018 - deliberate exception for demonstration
    except Exception as exc:
        logger.info("2. Enhanced error logging (with exc_info=True):")
        logger.error("Error in demo callback: %s", exc, exc_info=True)

    logger.info("=== Key Differences ===")
    logger.info("- Old way: Only shows the error message")
    logger.info("- New way: Shows full traceback with file names, line numbers, and call stack")
    logger.info("- This helps identify exactly where the error occurred and why")


def monitoring_tips():
    """Provide tips for monitoring the application for errors."""

    logger.info("")
    logger.info("=== Error Monitoring Tips ===")
    logger.info("1. Real-time log monitoring:")
    logger.info("   tail -f logs/casino_calendar_prod.log")
    logger.info("")
    logger.info("2. Filter for errors only:")
    logger.info("   grep 'ERROR' logs/casino_calendar_prod.log")
    logger.info("")
    logger.info("3. Look for specific callback errors:")
    logger.info("   grep 'show_event_modal callback' logs/casino_calendar_prod.log")
    logger.info("")
    logger.info("4. In VS Code, you can:")
    logger.info("   - Use Ctrl+F to search for 'ERROR' in the log file")
    logger.info("   - Look for 'Traceback' entries that follow ERROR messages")
    logger.info("   - Check line numbers mentioned in tracebacks")
    logger.info("")
    logger.info("5. Common error triggers to test:")
    logger.info("   - Click on an event in the calendar grid")
    logger.info("   - Click on a day column header")
    logger.info("   - Use the navigation buttons")
    logger.info("   - Toggle the overflow events")


def debugging_steps():
    """Provide step-by-step debugging guidance."""

    logger.info("")
    logger.info("=== Debugging Steps for show_event_modal Error ===")
    logger.info("Step 1: Run the application")
    logger.info("   python app.py")
    logger.info("")
    logger.info("Step 2: Trigger the error")
    logger.info("   - Open the application in your browser")
    logger.info("   - Try clicking on different calendar elements")
    logger.info("   - Look for actions that cause the modal to open")
    logger.info("")
    logger.info("Step 3: Check the logs")
    logger.info("   - Look at logs/casino_calendar_prod.log")
    logger.info("   - Search for 'ERROR' messages")
    logger.info("   - Look for the full traceback after 'show_event_modal callback:'")
    logger.info("")
    logger.info("Step 4: Analyze the traceback")
    logger.info("   - Note the file and line number where the error occurred")
    logger.info("   - Check the exception type (ValueError, KeyError, etc.)")
    logger.info("   - Review the code at that location")
    logger.info("")
    logger.info("Step 5: Common issues to check:")
    logger.info("   - Missing data in the DataFrame")
    logger.info("   - Invalid date formats")
    logger.info("   - Null/None values in expected data")
    logger.info("   - Mismatched data types")


if __name__ == "__main__":
    demonstrate_error_logging()
    monitoring_tips()
    debugging_steps()
