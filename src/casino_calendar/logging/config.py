"""Central logging configuration for the Casino Calendar application.

This module provides centralized logging setup with the following features:
- Colored console output with custom formatting
- File logging with automatic rotation
- HTTP request log suppression (configurable via SUPPRESS_HTTP_LOGS)
- Environment-based configuration (LOG_LEVEL, LOG_FILE)
- Production-ready setup with log cleanup
"""

import atexit
import logging
import os
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable, Iterable, Optional

from casino_calendar import settings
from casino_calendar.logging import rotation as rotation_utils

# Ensure logging picks up environment variables loaded centrally via settings.
ENV_FILE: Path = settings.ENV_FILE

# Import our custom log rotation utilities with safe typing
CleanupFn = Callable[[str, int], int]
SetupFn = Callable[[str, str, int, int, int, bool], logging.Logger]

cleanup_old_logs: CleanupFn = rotation_utils.cleanup_old_logs
setup_rotating_logger: SetupFn = rotation_utils.setup_rotating_logger


_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

_MINIMAL_LOG_PREFIXES = (
    "Production logging initialized",
    "Logging system initialized",
    "Logging system shutting down",
)

_HTTP_LOGGER_NAMES = (
    "werkzeug",
    "waitress",
    "gunicorn.access",
    "uvicorn.access",
    "cherrypy.access",
)
_MAINTENANCE_LOGGER_BLOCKLIST = (
    "casino_calendar.tests",
    "casino_calendar.scripts.run_tests",
)
_MAINTENANCE_EMBEDDED_LOG_RE = re.compile(
    r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| (DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+\|"
)


_HTTP_LOG_BASE_PATH: Optional[Path] = None
_HTTP_FILE_HANDLER: Optional[RotatingFileHandler] = None
_HANDLER_ROLE_ATTR = "_casino_handler_role"
_CONSOLE_ROLE = "console"
_FILE_ROLE = "file"


def _http_logs_are_suppressed() -> bool:
    return os.getenv("SUPPRESS_HTTP_LOGS", "True").lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def _derive_http_log_path(base_path: Path) -> Path:
    suffix = base_path.suffix or ".log"
    stem = base_path.stem

    if "casino_calendar" in stem:
        filename = f"casino_calendar_http{suffix}"
    else:
        filename = f"{stem}_http{suffix}"

    return base_path.with_name(filename)


def _teardown_http_log_handler() -> None:
    global _HTTP_FILE_HANDLER

    handler = _HTTP_FILE_HANDLER
    if handler is None:
        _configure_http_log_file_routing()
        return

    for logger_name in _HTTP_LOGGER_NAMES:
        http_logger = logging.getLogger(logger_name)
        if handler in http_logger.handlers:
            http_logger.removeHandler(handler)

    try:
        handler.close()
    finally:
        _HTTP_FILE_HANDLER = None
        _configure_http_log_file_routing()


def _ensure_http_file_handler(base_path: Path) -> None:
    global _HTTP_FILE_HANDLER, _HTTP_LOG_BASE_PATH

    _HTTP_LOG_BASE_PATH = base_path

    if _http_logs_are_suppressed():
        _teardown_http_log_handler()
        return

    http_log_path = _derive_http_log_path(base_path)
    http_log_path.parent.mkdir(parents=True, exist_ok=True)

    if _HTTP_FILE_HANDLER is not None:
        existing_path = Path(_HTTP_FILE_HANDLER.baseFilename)
        if existing_path == http_log_path:
            _configure_http_log_file_routing()
            return
        _teardown_http_log_handler()

    handler = RotatingFileHandler(
        str(http_log_path),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(CasinoCalendarFormatter(use_colors=False))
    setattr(handler, "_casino_http_handler", True)

    _HTTP_FILE_HANDLER = handler
    _configure_http_log_file_routing()


def _configure_http_log_file_routing() -> None:
    handler = _HTTP_FILE_HANDLER

    for logger_name in _HTTP_LOGGER_NAMES:
        http_logger = logging.getLogger(logger_name)

        for existing in list(http_logger.handlers):
            if getattr(existing, "_casino_http_handler", False) and existing is not handler:
                http_logger.removeHandler(existing)
                try:
                    existing.close()
                except Exception:
                    pass

        if handler is not None and handler not in http_logger.handlers:
            http_logger.addHandler(handler)
            http_logger.propagate = False
            if http_logger.level == logging.NOTSET or http_logger.level > logging.INFO:
                http_logger.setLevel(logging.INFO)


def _is_minimal_log_mode() -> bool:
    value = os.getenv("CASINO_MINIMAL_TEST_LOG", "").lower()
    return value not in ("", "0", "false", "off", "no")


def _should_apply_minimal_filter(log_path: Path) -> bool:
    if not _is_minimal_log_mode():
        return False
    configured = os.getenv("LOG_FILE")
    candidates = {"casino_calendar.log", "casino_calendar_prod.log"}
    if configured:
        candidates.add(Path(configured).name)
    return log_path.name in candidates


class _MinimalTestFilter(logging.Filter):
    """Filter that keeps only bootstrap/shutdown log lines in test mode."""

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        if not _is_minimal_log_mode():
            return True
        message = record.getMessage()
        return message.startswith(_MINIMAL_LOG_PREFIXES)


class _HttpSuppressionFilter(logging.Filter):
    """Filter that suppresses HTTP access logs and emits a single notice."""

    def __init__(self, logger_names: Iterable[str]):
        super().__init__()
        self._logger_names = tuple(logger_names)
        self._notified = False

    def _matches(self, record: logging.LogRecord) -> bool:
        return any(record.name == name or record.name.startswith(f"{name}.") for name in self._logger_names)

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        if self._matches(record) and record.levelno < logging.WARNING:
            if not self._notified:
                self._emit_notice(record)
                self._notified = True
            return False
        return True

    def _emit_notice(self, record: logging.LogRecord) -> None:
        message = (
            "HTTP request log suppressed from " f"{record.name} (set SUPPRESS_HTTP_LOGS=false to view HTTP traffic)"
        )
        try:
            print(message)
        except Exception:
            try:
                sys.stdout.write(message + "\n")
            except Exception:
                pass


class _MaintenanceDedupFilter(logging.Filter):
    """Filter that drops duplicate entries from the maintenance log."""

    def __init__(self, blocked_prefixes: Iterable[str]):
        super().__init__()
        self._blocked_prefixes = tuple(blocked_prefixes)

    def _is_blocked_logger(self, name: str) -> bool:
        for prefix in self._blocked_prefixes:
            if name == prefix or name.startswith(f"{prefix}."):
                return True
        return False

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        if self._is_blocked_logger(record.name):
            return False
        message = record.getMessage()
        if _MAINTENANCE_EMBEDDED_LOG_RE.search(message):
            return False
        return True


_HTTP_SUPPRESSION_FILTER: Optional[_HttpSuppressionFilter] = None
_MAINTENANCE_DEDUP_FILTER: Optional[_MaintenanceDedupFilter] = None


def _get_http_suppression_filter() -> _HttpSuppressionFilter:
    global _HTTP_SUPPRESSION_FILTER
    if _HTTP_SUPPRESSION_FILTER is None:
        _HTTP_SUPPRESSION_FILTER = _HttpSuppressionFilter(_HTTP_LOGGER_NAMES)
    else:
        _HTTP_SUPPRESSION_FILTER._notified = False
    return _HTTP_SUPPRESSION_FILTER


def _get_maintenance_dedup_filter() -> _MaintenanceDedupFilter:
    global _MAINTENANCE_DEDUP_FILTER
    if _MAINTENANCE_DEDUP_FILTER is None:
        _MAINTENANCE_DEDUP_FILTER = _MaintenanceDedupFilter(_MAINTENANCE_LOGGER_BLOCKLIST)
    return _MAINTENANCE_DEDUP_FILTER


def _apply_filter(handler: logging.Handler, filter_instance: Optional[logging.Filter]) -> None:
    if filter_instance is None:
        handler.filters = [existing for existing in handler.filters if not isinstance(existing, _HttpSuppressionFilter)]
        return
    if filter_instance not in handler.filters:
        handler.addFilter(filter_instance)


def _find_handler(logger: logging.Logger, role: str) -> Optional[logging.Handler]:
    for handler in logger.handlers:
        if getattr(handler, _HANDLER_ROLE_ATTR, None) == role:
            return handler
    return None


def _ensure_console_handler(
    logger: logging.Logger,
    *,
    level: int,
    formatter: logging.Formatter,
    http_filter: Optional[logging.Filter],
    stream: Optional[object] = None,
    role: str = _CONSOLE_ROLE,
) -> None:
    handler = _find_handler(logger, role)
    if handler is None:
        target_stream = stream if stream is not None else sys.stderr
        handler = logging.StreamHandler(target_stream)  # type: ignore[arg-type]
        setattr(handler, _HANDLER_ROLE_ATTR, role)
        logger.addHandler(handler)

    handler.setLevel(level)
    handler.setFormatter(formatter)
    _apply_filter(handler, http_filter)


def _ensure_file_handler(
    logger: logging.Logger,
    *,
    log_path: Path,
    level: int,
    max_bytes: int,
    backup_count: int,
    formatter: logging.Formatter,
    minimal_filter: Optional[logging.Filter],
    role: str = _FILE_ROLE,
) -> None:
    handler = _find_handler(logger, role)
    if handler is not None and isinstance(handler, RotatingFileHandler):
        existing_path = Path(handler.baseFilename)
        if existing_path != log_path:
            logger.removeHandler(handler)
            try:
                handler.close()
            finally:
                handler = None
    else:
        handler = None

    if handler is None:
        handler = RotatingFileHandler(
            str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        setattr(handler, _HANDLER_ROLE_ATTR, role)
        logger.addHandler(handler)

    handler.setLevel(level)
    handler.setFormatter(formatter)
    if minimal_filter is None:
        handler.filters = [existing for existing in handler.filters if not isinstance(existing, _MinimalTestFilter)]
    elif minimal_filter not in handler.filters:
        handler.addFilter(minimal_filter)


class CasinoCalendarFormatter(logging.Formatter):
    """Custom formatter with enhanced formatting for different log levels."""

    # Color codes for console output
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def __init__(self, use_colors: bool = True):
        """Initialize formatter with optional color support."""
        self.use_colors = use_colors and sys.stderr.isatty()
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with timestamp, level, module, and message."""
        # Create base format
        log_format = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"

        # Add colors for console output
        if self.use_colors and record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS["RESET"]
            log_format = f"{color}{log_format}{reset}"

        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def _coerce_log_level(level_name: str, fallback: int = logging.INFO) -> int:
    """Convert level name to logging constant with fallback."""

    return _LEVEL_MAP.get(level_name.upper(), fallback)


def get_log_level(env_var: str = "LOG_LEVEL", default: str = "INFO") -> int:
    """Get log level from an environment variable with optional override."""

    configured = os.getenv(env_var)
    fallback = _coerce_log_level(default, logging.INFO)
    if configured:
        return _coerce_log_level(configured, fallback)
    return fallback


def _suppress_http_logs() -> Optional[logging.Filter]:
    """Suppress HTTP request/response logs from console output.

    This function sets the logging level for common web server loggers
    to WARNING or higher, which prevents GET/POST request logs from
    appearing in the console while keeping them in log files.

    Can be controlled by SUPPRESS_HTTP_LOGS environment variable (default: True).
    """
    # Check if HTTP log suppression is enabled (default: True)
    suppress_enabled = _http_logs_are_suppressed()

    if not suppress_enabled:
        global _HTTP_SUPPRESSION_FILTER
        _HTTP_SUPPRESSION_FILTER = None
        if _HTTP_LOG_BASE_PATH is not None:
            _ensure_http_file_handler(_HTTP_LOG_BASE_PATH)
        else:
            _configure_http_log_file_routing()
        return None  # HTTP logs will be shown normally

    _teardown_http_log_handler()

    filter_instance = _get_http_suppression_filter()

    for logger_name in _HTTP_LOGGER_NAMES:
        http_logger = logging.getLogger(logger_name)
        http_logger.propagate = False
        console_handlers = [h for h in http_logger.handlers if isinstance(h, logging.StreamHandler)]
        for handler in console_handlers:
            http_logger.removeHandler(handler)

    return filter_instance


def setup_logger(name: str, log_file: Optional[str] = None, level: Optional[int] = None) -> logging.Logger:
    """Setup and configure a logger with console and optional file output.

    Args:
        name: Logger name (typically __name__)
        log_file: Optional file path for log output
        level: Optional explicit logging level for the logger/console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    resolved_level = level if level is not None else get_log_level()
    logger.setLevel(resolved_level)

    # Suppress noisy HTTP request logs from console (but keep in file)
    http_filter = _suppress_http_logs()

    _ensure_console_handler(
        logger,
        level=resolved_level,
        formatter=CasinoCalendarFormatter(use_colors=True),
        http_filter=http_filter,
        stream=sys.stderr,
    )

    # File handler - use log_file parameter or fall back to LOG_FILE env var
    file_path = log_file or os.getenv("LOG_FILE")
    if file_path:
        log_path = Path(file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Use larger rotation settings for development
        max_bytes = 10 * 1024 * 1024  # 10MB per file
        backup_count = 5  # Keep 5 backup files

        minimal_filter = _MinimalTestFilter() if _should_apply_minimal_filter(log_path) else None
        _ensure_file_handler(
            logger,
            log_path=log_path,
            level=logging.DEBUG,
            max_bytes=max_bytes,
            backup_count=backup_count,
            formatter=CasinoCalendarFormatter(use_colors=False),
            minimal_filter=minimal_filter,
        )
        _ensure_http_file_handler(log_path)

    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False

    return logger


def setup_production_logger(name: str = "casino_calendar") -> logging.Logger:
    """Setup logger with production-ready log rotation and cleanup.

    This function sets up a logger with:
    - Uses LOG_FILE environment variable for file path
    - Automatic log rotation (10MB files, 5 backups)
    - Cleanup of old logs (30 days retention)
    - Appropriate log levels for production

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    # Suppress HTTP request logs from console
    http_filter = _suppress_http_logs()

    # Get log file from environment variable, fallback to default
    log_file_env = os.getenv("LOG_FILE")
    if not log_file_env:
        log_dir = Path("logs")
        log_file = log_dir / "casino_calendar.log"
    else:
        log_file = Path(log_file_env)

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    archive_directory = log_file.parent / "archive"
    archive_mode = os.getenv("ARCHIVE_APP_LOG_ON_STARTUP", "false").lower()
    if log_file.exists():
        try:
            if archive_mode in {"true", "1", "yes", "on", "move"}:
                archived_path = rotation_utils.archive_current_log(
                    str(log_file),
                    archive_dir=str(archive_directory),
                    move=True,
                )
                print(f"Archived existing log to: {archived_path}")
            elif archive_mode == "copy":
                archived_path = rotation_utils.copy_current_log(
                    str(log_file),
                    archive_dir=str(archive_directory),
                )
                print(f"Copied existing log to: {archived_path}")
            # Always ensure archive structure is normalised, but do not
            # move the active log unless explicitly requested.
            rotation_utils.normalise_archives(str(log_file), str(archive_directory))
        except Exception as exc:
            print(f"Warning: Could not process archive for {log_file}: {exc}")

    # Clean up old logs (keep last 30 days)
    try:
        deleted_count = cleanup_old_logs(str(log_file.parent), 30)
        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} old log files")
    except Exception as e:
        print(f"Warning: Could not clean up old logs: {e}")

    # Use custom rotating logger for production
    minimal_filter: Optional[_MinimalTestFilter] = None
    if _should_apply_minimal_filter(log_file):
        minimal_filter = _MinimalTestFilter()

    logger = setup_rotating_logger(
        name,
        str(log_file),
        logging.INFO,  # Production level
        10 * 1024 * 1024,  # 10MB
        5,
        True,
    )
    if http_filter is not None:
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                _apply_filter(handler, http_filter)
                setattr(handler, _HANDLER_ROLE_ATTR, _CONSOLE_ROLE)
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename).name == log_file.name:
            _ensure_http_file_handler(Path(handler.baseFilename))
            setattr(handler, _HANDLER_ROLE_ATTR, _FILE_ROLE)
            if minimal_filter:
                handler.addFilter(minimal_filter)
        if isinstance(handler, logging.StreamHandler):
            handler.setFormatter(CasinoCalendarFormatter(use_colors=True))
        elif isinstance(handler, logging.FileHandler):
            handler.setFormatter(CasinoCalendarFormatter(use_colors=False))
    logger.info("Configured production logging with rotation")

    if not getattr(logger, "_casino_shutdown_registered", False):

        def _log_shutdown() -> None:
            if logger.handlers:
                logger.info("Shutting down logging system")

        atexit.register(_log_shutdown)
        logger._casino_shutdown_registered = True  # type: ignore[attr-defined]

    return logger


def get_maintenance_log_level() -> int:
    """Return the configured maintenance log level (defaults to INFO)."""

    return get_log_level("MAINTENANCE_LOG_LEVEL", default="INFO")


def get_maintenance_log_path() -> Path:
    """Resolve the maintenance log file path, ensuring the directory exists."""

    override = os.getenv("MAINTENANCE_LOG_FILE")
    if override:
        path = Path(override).expanduser()
    else:
        path = Path("logs") / "casino_calendar_maintenance.log"

        legacy_path = Path("logs") / "maintenance" / "casino_calendar_maintenance.log"
        if legacy_path.exists() and not path.exists():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                legacy_path.rename(path)
            except Exception:
                path = legacy_path

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def setup_maintenance_logger(
    name: str = "casino_calendar.maintenance",
) -> logging.Logger:
    """Configure a logger for setup, cleanup, and maintenance scripts."""

    logger = logging.getLogger(name)
    level = get_maintenance_log_level()
    logger.setLevel(logging.DEBUG)

    log_path = get_maintenance_log_path()

    _ensure_file_handler(
        logger,
        log_path=log_path,
        level=logging.DEBUG,
        max_bytes=5 * 1024 * 1024,
        backup_count=3,
        formatter=CasinoCalendarFormatter(use_colors=False),
        minimal_filter=None,
        role=f"{_FILE_ROLE}_maintenance",
    )
    _ensure_http_file_handler(log_path)

    file_handler = _find_handler(logger, f"{_FILE_ROLE}_maintenance")
    if file_handler is not None:
        dedup_filter = _get_maintenance_dedup_filter()
        if dedup_filter not in file_handler.filters:
            file_handler.addFilter(dedup_filter)

    http_filter = _suppress_http_logs()

    _ensure_console_handler(
        logger,
        level=level,
        formatter=logging.Formatter("%(message)s"),
        http_filter=http_filter,
        stream=sys.__stdout__,
        role=f"{_CONSOLE_ROLE}_maintenance",
    )

    logger.propagate = False

    return logger


def log_function_call(logger: logging.Logger, func_name: str, **kwargs):
    """Log function call with parameters (for debugging)."""
    if kwargs:
        logger.debug("%s called with %d parameter(s)", func_name, len(kwargs))
        for key, value in kwargs.items():
            logger.debug("%s parameter %s=%r", func_name, key, value)
    else:
        logger.debug("%s called with no parameters", func_name)


def log_performance(logger: logging.Logger, operation: str, start_time: float, end_time: float):
    """Log performance metrics for operations."""
    duration = end_time - start_time
    logger.info("%s completed in %.3f seconds", operation, duration)


def log_dataframe_info(logger: logging.Logger, df, description: str = "DataFrame"):
    """Log useful information about a pandas DataFrame."""
    if df is not None and hasattr(df, "shape"):
        rows, cols = df.shape
        logger.debug("%s size: %d rows x %d columns", description, rows, cols)
        if hasattr(df, "columns"):
            column_names = ", ".join(str(col) for col in df.columns)
            logger.debug("%s columns: %s", description, column_names)
    else:
        logger.warning("%s is None or invalid", description)


# Global application logger instance - use production setup
app_logger = setup_production_logger("casino_calendar")

# Log startup
app_logger.info("Logging system initialized")
app_logger.debug("Log level: %s", logging.getLevelName(get_log_level()))
