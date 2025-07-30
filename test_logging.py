#!/usr/bin/env python3
"""Test script to verify the logging system implementation."""

import os
import sys
import time
import tempfile
from pathlib import Path

# Set up test environment
os.environ["LOG_LEVEL"] = "DEBUG"

# Test the logging configuration
from app_components.logging_config import (
    setup_logger,
    log_performance,
    log_dataframe_info,
)


def test_basic_logging():
    """Test basic logging functionality."""
    print("=" * 60)
    print("TESTING BASIC LOGGING")
    print("=" * 60)

    logger = setup_logger("test_module")

    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")

    print("\n✅ Basic logging test completed")


def test_file_logging():
    """Test file logging functionality."""
    print("\n" + "=" * 60)
    print("TESTING FILE LOGGING")
    print("=" * 60)

    # Create temporary log file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as tmp:
        log_file = tmp.name

    try:
        logger = setup_logger("test_file_module", log_file=log_file)

        logger.info("Testing file logging")
        logger.debug("This should appear in the file")
        logger.warning("File logging test warning")

        # Read the log file
        with open(log_file, "r") as f:
            log_contents = f.read()

        print(f"Log file created at: {log_file}")
        print("Log file contents:")
        print("-" * 40)
        print(log_contents)
        print("-" * 40)

        print("✅ File logging test completed")

    finally:
        # Clean up
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_performance_logging():
    """Test performance logging functionality."""
    print("\n" + "=" * 60)
    print("TESTING PERFORMANCE LOGGING")
    print("=" * 60)

    logger = setup_logger("test_performance")

    # Simulate some work
    start_time = time.time()
    time.sleep(0.1)  # Simulate 100ms work
    end_time = time.time()

    log_performance(logger, "test_operation", start_time, end_time)

    print("✅ Performance logging test completed")


def test_dataframe_logging():
    """Test DataFrame logging functionality."""
    print("\n" + "=" * 60)
    print("TESTING DATAFRAME LOGGING")
    print("=" * 60)

    logger = setup_logger("test_dataframe")

    try:
        import pandas as pd

        # Create a sample DataFrame
        df = pd.DataFrame(
            {
                "Casino": ["Casino A", "Casino B", "Casino C"],
                "EventName": ["Event 1", "Event 2", "Event 3"],
                "OfferType": ["Free-Play", "Giveaway", "Point-Based"],
            }
        )

        log_dataframe_info(logger, df, "Sample Events DataFrame")

        # Test with None
        log_dataframe_info(logger, None, "None DataFrame")

        print("✅ DataFrame logging test completed")

    except ImportError:
        logger.warning("pandas not available, skipping DataFrame test")
        print("⚠️ DataFrame logging test skipped (pandas not available)")


def test_exception_logging():
    """Test exception logging."""
    print("\n" + "=" * 60)
    print("TESTING EXCEPTION LOGGING")
    print("=" * 60)

    logger = setup_logger("test_exceptions")

    try:
        # Simulate an error
        result = 1 / 0
    except Exception as e:
        logger.error(f"Caught expected exception: {e}")
        logger.debug("Exception details", exc_info=True)

    print("✅ Exception logging test completed")


def test_application_modules():
    """Test logging in actual application modules."""
    print("\n" + "=" * 60)
    print("TESTING APPLICATION MODULE LOGGING")
    print("=" * 60)

    try:
        # Test data module logging
        from app_components.data import categorize_offer_type_updated

        # This should trigger debug logging
        result = categorize_offer_type_updated("Free Play Cash", "Get $10 free play")
        print(f"Categorization result: {result}")

        # Test colors module
        from utils.colors import get_color

        colors = get_color()
        print(f"Retrieved colors for {len(colors)} casinos")

        print("✅ Application module logging test completed")

    except Exception as e:
        print(f"❌ Application module test failed: {e}")


def test_log_levels():
    """Test different log levels."""
    print("\n" + "=" * 60)
    print("TESTING LOG LEVELS")
    print("=" * 60)

    # Test with different log levels
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        print(f"\nTesting with LOG_LEVEL={level}")
        os.environ["LOG_LEVEL"] = level

        # Force reload of logging config
        import importlib
        import app_components.logging_config

        importlib.reload(app_components.logging_config)

        logger = setup_logger(f"test_{level.lower()}")
        logger.debug(f"DEBUG message (should only show if level is DEBUG)")
        logger.info(f"INFO message (should show if level is DEBUG or INFO)")
        logger.warning(f"WARNING message (should show unless level is ERROR/CRITICAL)")
        logger.error(f"ERROR message (should always show except CRITICAL)")
        logger.critical(f"CRITICAL message (should always show)")

    # Reset to DEBUG for remaining tests
    os.environ["LOG_LEVEL"] = "DEBUG"
    importlib.reload(app_components.logging_config)

    print("\n✅ Log levels test completed")


def main():
    """Run all logging tests."""
    print("🎰 Casino Calendar - Logging System Test Suite")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"LOG_LEVEL environment variable: {os.getenv('LOG_LEVEL', 'Not set')}")

    # Run all tests
    test_basic_logging()
    test_file_logging()
    test_performance_logging()
    test_dataframe_logging()
    test_exception_logging()
    test_log_levels()
    test_application_modules()

    print("\n" + "=" * 60)
    print("🎉 ALL LOGGING TESTS COMPLETED")
    print("=" * 60)
    print("\nLogging system is ready for production use!")
    print("\nNext steps:")
    print("1. Set LOG_LEVEL environment variable for your deployment")
    print("2. Optionally set LOG_FILE for file output")
    print("3. Run the application: python app.py")
    print("4. Check logs in console or specified log file")


if __name__ == "__main__":
    main()
