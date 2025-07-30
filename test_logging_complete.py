#!/usr/bin/env python3
"""Test script to verify logging and app functionality."""

print("=== Testing Logging System ===")

# Test environment loading
import os

print(f"LOG_LEVEL: {os.getenv('LOG_LEVEL', 'Not set')}")
print(f"LOG_FILE: {os.getenv('LOG_FILE', 'Not set')}")

# Test logging
from app_components.logging_config import setup_logger

logger = setup_logger("test_script")

logger.info("Starting test script")
logger.debug("This is a debug message")
logger.warning("This is a warning message")
logger.error("This is an error message")

# Test app import
try:
    print("\n=== Testing App Import ===")
    import app

    logger.info("App imported successfully")
    print("✅ App import successful")
except Exception as e:
    logger.error(f"Failed to import app: {e}")
    print(f"❌ App import failed: {e}")

logger.info("Test script completed")
print("\n=== Test Complete ===")
print("Check app.log for detailed logging output!")
