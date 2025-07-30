#!/usr/bin/env python3
"""
Casino Calendar - Logging System Demo

This script demonstrates the logging capabilities implemented
throughout the Casino Calendar application.
"""

import os
import time

# Set log level for demonstration
os.environ["LOG_LEVEL"] = "DEBUG"

from app_components.logging_config import setup_logger, log_performance


def main():
    """Demonstrate the logging system."""

    print("🎰 Casino Calendar - Logging System Demo")
    print("=" * 50)

    # Initialize logger
    logger = setup_logger(__name__)

    logger.info("Starting logging system demonstration")

    # Demonstrate different log levels
    logger.debug("This is a DEBUG message - shows detailed information")
    logger.info("This is an INFO message - shows general information")
    logger.warning("This is a WARNING message - shows potential issues")
    logger.error("This is an ERROR message - shows errors that occurred")
    logger.critical("This is a CRITICAL message - shows critical failures")

    # Demonstrate performance logging
    logger.info("Demonstrating performance logging...")
    start_time = time.time()
    time.sleep(0.05)  # Simulate some work
    end_time = time.time()
    log_performance(logger, "demo_operation", start_time, end_time)

    # Test application modules
    try:
        logger.info("Testing application modules with logging...")

        # Test data categorization (shows debug logging)
        from app_components.data import categorize_offer_type_updated

        result = categorize_offer_type_updated("Free Play Bonus", "Get $25 free play")
        logger.info(f"Categorization result: {result}")

        # Test color system (shows debug logging)
        from utils.colors import get_color

        colors = get_color()
        logger.info(f"Loaded colors for {len(colors)} casinos")

        logger.info("Application modules tested successfully")

    except Exception as e:
        logger.error(f"Error testing application modules: {e}")

    logger.info("Logging system demonstration completed")

    print("\n" + "=" * 50)
    print("✅ Logging system is working correctly!")
    print("\nTo use different log levels:")
    print("LOG_LEVEL=INFO python demo_logging.py")
    print("LOG_LEVEL=WARNING python demo_logging.py")
    print("LOG_LEVEL=ERROR python demo_logging.py")
    print("\nTo enable file logging:")
    print("LOG_FILE=app.log python demo_logging.py")


if __name__ == "__main__":
    main()
