"""Tests for the logging system implementation."""

import contextlib
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from casino_calendar.logging import config as logging_config


def test_get_log_level_default():
    """Test default log level is INFO."""
    with patch.dict(os.environ, {}, clear=True):
        level = logging_config.get_log_level()
        assert level == 20  # logging.INFO


def test_get_log_level_from_env():
    """Test log level can be set via environment variable."""
    with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
        level = logging_config.get_log_level()
        assert level == 10  # logging.DEBUG

    with patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}):
        level = logging_config.get_log_level()
        assert level == 30  # logging.WARNING


def test_get_maintenance_log_level_defaults():
    """Maintenance log level falls back to INFO and honors overrides."""
    with patch.dict(os.environ, {}, clear=True):
        assert logging_config.get_maintenance_log_level() == 20  # logging.INFO

    with patch.dict(os.environ, {"MAINTENANCE_LOG_LEVEL": "ERROR"}):
        assert logging_config.get_maintenance_log_level() == 40  # logging.ERROR


def test_get_maintenance_log_path_default_moves_legacy(tmp_path, monkeypatch):
    """Legacy maintenance log is moved into the new default location."""
    monkeypatch.chdir(tmp_path)
    legacy_dir = Path("logs") / "maintenance"
    legacy_dir.mkdir(parents=True)
    legacy_file = legacy_dir / "casino_calendar_maintenance.log"
    legacy_file.write_text("legacy")

    monkeypatch.delenv("MAINTENANCE_LOG_FILE", raising=False)
    resolved = logging_config.get_maintenance_log_path()

    assert resolved == Path("logs") / "casino_calendar_maintenance.log"
    assert resolved.exists()
    assert not legacy_file.exists()


def test_get_maintenance_log_path_override(tmp_path, monkeypatch):
    """Maintenance log path uses override and creates parent directory."""
    custom_path = tmp_path / "maintenance" / "custom.log"
    monkeypatch.setenv("MAINTENANCE_LOG_FILE", str(custom_path))

    resolved = logging_config.get_maintenance_log_path()

    assert resolved == custom_path
    assert resolved.parent.exists()


def test_setup_logger_basic():
    """Test basic logger setup."""
    logger = logging_config.setup_logger("test_logger")
    assert logger.name == "test_logger"
    assert len(logger.handlers) > 0

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_setup_logger_with_file():
    """Test logger setup with file output."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as tmp:
        log_file = tmp.name

    try:
        logger = logging_config.setup_logger("test_file_logger", log_file=log_file)
        assert len(logger.handlers) == 2  # Console + file handlers

        logger.info("Test log message")

        with open(log_file, "r", encoding="utf-8") as file_handle:
            content = file_handle.read()
            assert "Test log message" in content
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()

        if os.path.exists(log_file):
            try:
                os.unlink(log_file)
            except PermissionError:
                pass  # Windows file locking issue


def test_http_access_logs_written_when_not_suppressed(tmp_path, monkeypatch):
    """HTTP access logs should be routed into log files when suppression is disabled."""

    monkeypatch.setenv("SUPPRESS_HTTP_LOGS", "false")

    http_logger = logging.getLogger("werkzeug")
    original_handlers = http_logger.handlers[:]
    for handler in original_handlers:
        http_logger.removeHandler(handler)

    log_path = tmp_path / "application.log"
    http_log_path = tmp_path / "application_http.log"
    logger = logging_config.setup_logger("test_http_logging", log_file=str(log_path))

    try:
        http_logger.info("Werkzeug served GET /ping 200")

        for handler in logger.handlers:
            if hasattr(handler, "flush"):
                handler.flush()

        assert log_path.exists(), "Expected application log file to be created"
        assert http_log_path.exists(), "Expected dedicated HTTP log file to be created"

        content = log_path.read_text(encoding="utf-8")
        http_content = http_log_path.read_text(encoding="utf-8")
        assert "Werkzeug served GET /ping 200" not in content
        assert "Werkzeug served GET /ping 200" in http_content
    finally:
        for handler in http_logger.handlers[:]:
            http_logger.removeHandler(handler)

        for handler in original_handlers:
            http_logger.addHandler(handler)

        monkeypatch.setenv("SUPPRESS_HTTP_LOGS", "true")
        logging_config._suppress_http_logs()

        with contextlib.suppress(FileNotFoundError):
            os.remove(http_log_path)

        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()


def test_setup_maintenance_logger_writes_file(tmp_path, monkeypatch):
    """Maintenance logger writes to file and installs expected handlers."""
    log_path = tmp_path / "maintenance.log"
    monkeypatch.setenv("MAINTENANCE_LOG_FILE", str(log_path))
    monkeypatch.setenv("MAINTENANCE_LOG_LEVEL", "INFO")

    logger = logging_config.setup_maintenance_logger("test_maintenance_logger")

    try:
        logger.info("maintenance info message")
        logger.debug("maintenance debug message")

        assert log_path.exists()
        content = log_path.read_text(encoding="utf-8")
        assert "maintenance info message" in content
        assert "maintenance debug message" in content

        assert len(logger.handlers) == 2
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()


def test_setup_production_logger_archives_existing(tmp_path, monkeypatch):
    """Existing app log is archived on startup when enabled."""
    monkeypatch.chdir(tmp_path)
    log_dir = Path("logs")
    log_dir.mkdir()
    log_file = log_dir / "casino_calendar.log"
    log_file.write_text(
        "2025-09-01 10:00:00 | INFO     | casino_calendar | old log content\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("LOG_FILE", raising=False)
    monkeypatch.setenv("ARCHIVE_APP_LOG_ON_STARTUP", "move")
    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "0")

    logger = logging_config.setup_production_logger("test_archive_logger")

    try:
        assert log_file.exists()
        archive_dir = log_dir / "archive"
        all_file = archive_dir / "casino_calendar_all.log"
        assert all_file.exists()
        assert "old log content" in all_file.read_text(encoding="utf-8")
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()


def test_formatter():
    """Test custom formatter."""
    formatter = logging_config.CasinoCalendarFormatter(use_colors=False)

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
    from casino_calendar.dash_app.data.transforms import categorize_offer_type

    result = categorize_offer_type("Free Play", "Get free money")
    assert isinstance(result, str)


def test_app_import_with_logging():
    """Test that the main app can be imported with logging enabled."""
    try:
        import casino_calendar.dash_app.data.loader  # noqa: F401
        import casino_calendar.logging.config  # noqa: F401
        import casino_calendar.services.colors  # noqa: F401

        assert True
    except Exception as exc:  # pragma: no cover - defensive
        pytest.fail(f"Failed to import modules with logging: {exc}")


def test_minimal_log_mode_filters_production_messages(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    prod_log = log_dir / "casino_calendar_prod.log"
    monkeypatch.setenv("LOG_FILE", str(prod_log))
    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "1")

    logger = logging_config.setup_logger("minimal_filter", log_file=str(prod_log))

    try:
        logger.info("Some detailed message that should be suppressed")
        logger.info("Logging system shutting down")
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()

    content = prod_log.read_text(encoding="utf-8") if prod_log.exists() else ""
    assert "Some detailed message" not in content
    assert "Logging system shutting down" in content
