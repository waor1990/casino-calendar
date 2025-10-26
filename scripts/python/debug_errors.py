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

    logger.info("Starting error logging demonstration")

    # Simulate an error without exc_info (old way)
    try:
        _ = 10 / 0  # noqa: B018 - deliberate exception for demonstration
    except Exception as exc:
        logger.info("Legacy logging without traceback")
        logger.error("Error in demo callback: %s", exc)

    # Simulate an error with exc_info (new way)
    try:
        _ = 10 / 0  # noqa: B018 - deliberate exception for demonstration
    except Exception as exc:
        logger.info("Enhanced logging with traceback")
        logger.error("Error in demo callback: %s", exc, exc_info=True)

    logger.info("Legacy logging only reports the exception message")
    logger.info("Enhanced logging includes file names, line numbers, and stack details")
    logger.info("Full tracebacks make it easier to pinpoint the failure")


def monitoring_tips():
    """Provide tips for monitoring the application for errors."""

    logger.info("Error monitoring tips")
    logger.info("Monitor logs in real time: tail -f logs/casino_calendar_prod.log")
    logger.info("Filter for errors only: grep 'ERROR' logs/casino_calendar_prod.log")
    logger.info(
        "Search for callback errors: grep 'show_event_modal callback' logs/casino_calendar_prod.log"
    )
    logger.info("In VS Code use Ctrl+F for 'ERROR' and review Traceback sections")
    logger.info("Pay attention to line numbers referenced in tracebacks")
    logger.info(
        "Common triggers to reproduce: click events, day headers, navigation, and overflow toggles"
    )


def debugging_steps():
    """Provide step-by-step debugging guidance."""

    logger.info("Debugging steps for show_event_modal errors")
    logger.info("Run the application: python app.py")
    logger.info("Trigger the issue by interacting with calendar elements")
    logger.info("Review logs at logs/casino_calendar_prod.log and search for 'ERROR'")
    logger.info("Check for tracebacks following the show_event_modal callback entry")
    logger.info("Capture the file, line number, and exception type from the traceback")
    logger.info("Inspect the referenced code to confirm data assumptions")
    logger.info(
        "Common causes include missing data, invalid dates, null values, or mismatched types"
    )


if __name__ == "__main__":
    demonstrate_error_logging()
    monitoring_tips()
    debugging_steps()
