"""Tests for the logging system implementation."""

import contextlib
import importlib
import io
import json
import logging
import os
import re
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from unittest.mock import patch

import pytest

from casino_calendar.logging import app_logging
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


def test_setup_logging_is_idempotent(tmp_path, monkeypatch):
    log_file = tmp_path / "app.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    logger = app_logging.setup_logging("test_idempotent")
    handler_ids_first = [id(handler) for handler in logger.handlers]

    logger = app_logging.setup_logging("test_idempotent")
    handler_ids_second = [id(handler) for handler in logger.handlers]

    assert handler_ids_first == handler_ids_second
    assert len(logger.handlers) == 2

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_console_format_pattern(tmp_path, monkeypatch):
    log_stream = io.StringIO()
    log_file = tmp_path / "console.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "0")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    logger = app_logging.setup_logging("test_console", console_stream=log_stream, level=logging.INFO)
    logger.info("Console format check")

    output = log_stream.getvalue().strip()
    assert re.search(r"^[\w\.]+:\w+:\d+ \| Console format check$", output)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_file_format_and_rotation(tmp_path, monkeypatch):
    log_file = tmp_path / "app.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "0")
    monkeypatch.setenv("LOG_FILE_TZ", "LOCAL")

    logger = app_logging.setup_logging("test_file_format")
    logger.info("File format check")

    file_handler = next(handler for handler in logger.handlers if isinstance(handler, TimedRotatingFileHandler))
    file_handler.flush()
    content = log_file.read_text(encoding="utf-8")
    assert re.search(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3} \| INF \| [\w\.]+:\w+:\d+ \| "
        r"pid=\d+ tid=\d+ \| .* \| svc=\S+ env=\S+ req=\S+ user=\S+$",
        content,
    )

    file_handler.doRollover()

    rotated_files = list(tmp_path.glob("app.log.*"))
    assert rotated_files

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_context_enrichment_with_adapter(tmp_path, monkeypatch):
    log_file = tmp_path / "context.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "0")

    adapter = app_logging.get_context_logger(
        "test_context",
        request_id="req-123",
        user_id="user-42",
    )
    adapter.info("Context test")

    for handler in adapter.logger.handlers:
        if hasattr(handler, "flush"):
            handler.flush()

    content = log_file.read_text(encoding="utf-8")
    assert "req=req-123" in content
    assert "user=user-42" in content

    for handler in adapter.logger.handlers[:]:
        adapter.logger.removeHandler(handler)
        handler.close()


def test_env_toggles_log_dir_and_json(tmp_path, monkeypatch):
    monkeypatch.delenv("LOG_FILE", raising=False)
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("LOG_FILE_JSON", "true")
    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "0")
    monkeypatch.setenv("LOG_FILE_TZ", "LOCAL")

    logger = app_logging.setup_logging("test_json")
    logger.info("json payload")

    for handler in logger.handlers:
        if hasattr(handler, "flush"):
            handler.flush()

    log_file = Path(os.environ["LOG_DIR"]) / "app.log"
    assert log_file.exists()

    line = log_file.read_text(encoding="utf-8").strip()
    payload = json.loads(line)
    assert payload["message"] == "json payload"
    assert payload["level"] == "INFO"
    assert payload["tz"] == "LOCAL"

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_console_minimal_mode_trims_context(tmp_path, monkeypatch):
    log_stream = io.StringIO()
    log_file = tmp_path / "minimal_console.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "1")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    logger = app_logging.setup_logging("test_minimal_console", console_stream=log_stream, level=logging.INFO)
    logger.info("Minimal console check")

    output = log_stream.getvalue().strip()
    assert output == "Minimal console check"

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_console_utc_mode_omits_timestamp(tmp_path, monkeypatch):
    log_stream = io.StringIO()
    log_file = tmp_path / "utc_console.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    monkeypatch.setenv("LOG_CONSOLE_TZ", "UTC")
    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "0")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    logger = app_logging.setup_logging("test_console_utc", console_stream=log_stream, level=logging.INFO)
    logger.info("UTC console check")

    output = log_stream.getvalue().strip()
    assert not re.search(r"\d{2}:\d{2}:\d{2}", output)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_console_debug_context_suffix(tmp_path, monkeypatch):
    log_stream = io.StringIO()
    log_file = tmp_path / "debug_console.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "0")

    logger = app_logging.setup_logging("test_console_debug", console_stream=log_stream, level=logging.DEBUG)
    logger.info("Debug console check", extra={"request_id": "req-9", "user_id": "user-9"})

    output = log_stream.getvalue().strip()
    assert "req=req-9 user=user-9" in output

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_logging_import_ignores_cwd_dotenv(tmp_path, monkeypatch):
    """Logging config should not implicitly load dotenv files from the CWD."""
    tmp_env = tmp_path / ".env"
    tmp_env.write_text("LOG_LEVEL=CRITICAL\n", encoding="utf-8")

    log_path = tmp_path / "logs" / "deterministic_import.log"

    monkeypatch.chdir(tmp_path)

    with patch.dict(os.environ, {"LOG_FILE": str(log_path), "SUPPRESS_HTTP_LOGS": "true"}, clear=True):
        base_logger = logging.getLogger("casino_calendar")
        for handler in base_logger.handlers[:]:
            base_logger.removeHandler(handler)
            handler.close()

        fresh_logging_config = importlib.reload(logging_config)

        try:
            assert "LOG_LEVEL" not in os.environ
            assert fresh_logging_config.get_log_level() == logging.INFO
        finally:
            for handler in fresh_logging_config.app_logger.handlers[:]:
                fresh_logging_config.app_logger.removeHandler(handler)
                handler.close()


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
        app_logging._suppress_http_logs()

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

        for handler in logger.handlers:
            if hasattr(handler, "flush"):
                handler.flush()

        assert log_path.exists()
        content = log_path.read_text(encoding="utf-8")
        assert "maintenance info message" in content
        assert "maintenance debug message" in content

        assert len(logger.handlers) == 2
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()


def test_maintenance_logger_is_idempotent(tmp_path, monkeypatch):
    log_path = tmp_path / "maintenance.log"
    monkeypatch.setenv("MAINTENANCE_LOG_FILE", str(log_path))
    monkeypatch.setenv("MAINTENANCE_LOG_LEVEL", "INFO")
    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "0")

    logger = logging_config.setup_maintenance_logger("test_maintenance_idempotent")
    handler_ids_first = [id(handler) for handler in logger.handlers]

    logger = logging_config.setup_maintenance_logger("test_maintenance_idempotent")
    handler_ids_second = [id(handler) for handler in logger.handlers]

    assert handler_ids_first == handler_ids_second

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_setup_production_logger_archives_existing(tmp_path, monkeypatch):
    """Existing app log is archived on startup when enabled."""
    monkeypatch.chdir(tmp_path)
    log_dir = Path("logs")
    log_dir.mkdir()
    log_file = log_dir / "app.log"
    log_file.write_text(
        "2025-09-01T10:00:00.000 | INF | module:func:1 | pid=1 tid=1 | old log content | svc=app env=local req=- user=-\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("LOG_FILE", raising=False)
    monkeypatch.setenv("ARCHIVE_APP_LOG_ON_STARTUP", "move")
    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "0")

    logger = logging_config.setup_production_logger("test_archive_logger")

    try:
        assert log_file.exists()
        archive_dir = log_dir / "archive"
        all_file = archive_dir / "app_all.log"
        assert all_file.exists()
        assert "old log content" in all_file.read_text(encoding="utf-8")
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()


def test_console_formatter(monkeypatch):
    """Test custom console formatter."""
    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "0")
    formatter = app_logging.ConsoleFormatter(use_colors=False, use_rich_markup=False)

    record = logging.LogRecord(
        name="test_module",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
        func="test_func",
    )

    formatted = formatter.format(record)
    assert "test:test_func:1" in formatted
    assert "Test message" in formatted


def test_duplicate_filter_suppresses_file_duplicates(tmp_path, monkeypatch):
    log_file = tmp_path / "dedupe.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "0")

    logger = app_logging.setup_logging("test_dedupe", level=logging.INFO)
    for _ in range(5):
        logger.info("repeat me")

    for handler in logger.handlers:
        if isinstance(handler, TimedRotatingFileHandler):
            handler.flush()

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert "(+4 duplicates suppressed)" in lines[0]

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_redaction_in_console_and_file(tmp_path, monkeypatch):
    log_stream = io.StringIO()
    log_file = tmp_path / "redaction.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "0")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    logger = app_logging.setup_logging("test_redaction", console_stream=log_stream, level=logging.INFO)
    logger.info("token=abc Authorization: Bearer SECRET Cookie: foo=bar")

    for handler in logger.handlers:
        if hasattr(handler, "flush"):
            handler.flush()

    console_output = log_stream.getvalue()
    file_output = log_file.read_text(encoding="utf-8")

    for output in (console_output, file_output):
        assert "token=****" in output
        assert "authorization=****" in output.lower()
        assert "SECRET" not in output
        assert "foo=bar" not in output
        assert "cookie:" not in output.lower()

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


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
    prod_log = log_dir / "app.log"
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
