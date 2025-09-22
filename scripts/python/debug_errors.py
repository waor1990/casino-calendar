#!/usr/bin/env python3
"""
Error Debugging Guide for Casino Calendar Application

This script demonstrates how to trigger and view detailed error information
in the show_event_modal callback and other parts of the application.
"""

import logging


def demonstrate_error_logging():
    """Demonstrate how exc_info=True provides full tracebacks."""

    # Setup a logger similar to the app
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("error_demo")

    print("=== Error Logging Demonstration ===\n")

    # Simulate an error without exc_info (old way)
    try:
        # This will raise a division by zero error
        _ = 10 / 0
    except Exception as e:
        print("1. Old error logging (without exc_info):")
        logger.error(f"Error in demo callback: {e}")
        print()

    # Simulate an error with exc_info (new way)
    try:
        # This will raise a division by zero error with full traceback
        _ = 10 / 0
    except Exception as e:
        print("2. Enhanced error logging (with exc_info=True):")
        logger.error(f"Error in demo callback: {e}", exc_info=True)
        print()

    print("=== Key Differences ===")
    print("- Old way: Only shows the error message")
    print("- New way: Shows full traceback with file names, line numbers, and call stack")
    print("- This helps identify exactly where the error occurred and why")


def monitoring_tips():
    """Provide tips for monitoring the application for errors."""

    print("\n=== Error Monitoring Tips ===")
    print()
    print("1. Real-time log monitoring:")
    print("   tail -f logs/casino_calendar_prod.log")
    print()
    print("2. Filter for errors only:")
    print("   grep 'ERROR' logs/casino_calendar_prod.log")
    print()
    print("3. Look for specific callback errors:")
    print("   grep 'show_event_modal callback' logs/casino_calendar_prod.log")
    print()
    print("4. In VS Code, you can:")
    print("   - Use Ctrl+F to search for 'ERROR' in the log file")
    print("   - Look for 'Traceback' entries that follow ERROR messages")
    print("   - Check line numbers mentioned in tracebacks")
    print()
    print("5. Common error triggers to test:")
    print("   - Click on an event in the calendar grid")
    print("   - Click on a day column header")
    print("   - Use the navigation buttons")
    print("   - Toggle the overflow events")


def debugging_steps():
    """Provide step-by-step debugging guidance."""

    print("\n=== Debugging Steps for show_event_modal Error ===")
    print()
    print("Step 1: Run the application")
    print("   python app.py")
    print()
    print("Step 2: Trigger the error")
    print("   - Open the application in your browser")
    print("   - Try clicking on different calendar elements")
    print("   - Look for actions that cause the modal to open")
    print()
    print("Step 3: Check the logs")
    print("   - Look at logs/casino_calendar_prod.log")
    print("   - Search for 'ERROR' messages")
    print("   - Look for the full traceback after 'show_event_modal callback:'")
    print()
    print("Step 4: Analyze the traceback")
    print("   - Note the file and line number where the error occurred")
    print("   - Check the exception type (ValueError, KeyError, etc.)")
    print("   - Review the code at that location")
    print()
    print("Step 5: Common issues to check:")
    print("   - Missing data in the DataFrame")
    print("   - Invalid date formats")
    print("   - Null/None values in expected data")
    print("   - Mismatched data types")


if __name__ == "__main__":
    demonstrate_error_logging()
    monitoring_tips()
    debugging_steps()
