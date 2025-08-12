"""Tests for the logging system implementation."""

import os
import tempfile
from unittest.mock import patch

import pytest

from app_components.logging_config import (CasinoCalendarFormatter,
                                           get_log_level, setup_logger)


def test_get_log_level_default():
    """Test default log level is INFO."""
    with patch.dict(os.environ, {}, clear=True):
        level = get_log_level()
        assert level == 20  # logging.INFO


def test_get_log_level_from_env():
    """Test log level can be set via environment variable."""
    with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
        level = get_log_level()
        assert level == 10  # logging.DEBUG

    with patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}):
        level = get_log_level()
        assert level == 30  # logging.WARNING


def test_setup_logger_basic():
    """Test basic logger setup."""
    logger = setup_logger("test_logger")
    assert logger.name == "test_logger"
    assert len(logger.handlers) > 0


def test_setup_logger_with_file():
    """Test logger setup with file output."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as tmp:
        log_file = tmp.name

    try:
        logger = setup_logger("test_file_logger", log_file=log_file)
        assert len(logger.handlers) == 2  # Console + file handlers

        # Test that we can write to the log
        logger.info("Test log message")

        # Check file exists and has content
        with open(log_file, "r") as f:
            content = f.read()
            assert "Test log message" in content

    finally:
        # Clean up
        if os.path.exists(log_file):
            try:
                os.unlink(log_file)
            except PermissionError:
                pass  # Windows file locking issue


def test_formatter():
    """Test custom formatter."""
    formatter = CasinoCalendarFormatter(use_colors=False)

    # Create a dummy log record
    import logging

    record = logging.LogRecord(
        name="test_module",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    assert "INFO" in formatted
    assert "test_module" in formatted
    assert "Test message" in formatted


def test_data_module_logging():
    """Test that data module imports with logging."""
    from app_components.data import categorize_offer_type_updated

    # This should work without errors
    result = categorize_offer_type_updated("Free Play", "Get free money")
    assert isinstance(result, str)


def test_colors_module_logging():
    """Test that colors module imports with logging."""
    from utils.colors import get_color

    # This should work without errors
    colors = get_color()
    assert isinstance(colors, dict)


def test_app_import_with_logging():
    """Test that the main app can be imported with logging enabled."""
    # This is a basic smoke test to ensure our logging changes don't break imports
    try:
        import app_components.data
        import app_components.logging_config  # noqa: F401 - verify import side effects
        import utils.colors  # noqa: F401 - verify import side effects

        # If we get here without exceptions, the test passes
        assert True
    except Exception as e:
        pytest.fail(f"Failed to import modules with logging: {e}")
