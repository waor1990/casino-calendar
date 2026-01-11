"""Central logging configuration for the Casino Calendar application."""

from __future__ import annotations

import atexit
import logging
import os
import sys
import warnings
from pathlib import Path
from typing import Callable, Optional

from casino_calendar import settings
from casino_calendar.logging import app_logging
from casino_calendar.logging import rotation as rotation_utils

ENV_FILE: Path = settings.ENV_FILE

CleanupFn = Callable[[str, int], int]
SetupFn = Callable[[str, str, int, int, int, bool], logging.Logger]

cleanup_old_logs: CleanupFn = rotation_utils.cleanup_old_logs
setup_rotating_logger: SetupFn = rotation_utils.setup_rotating_logger

get_log_level = app_logging.get_log_level
ContextLoggerAdapter = app_logging.ContextLoggerAdapter
get_context_logger = app_logging.get_context_logger
setup_logging = app_logging.setup_logging


ConsoleFormatter = app_logging.ConsoleFormatter
FileFormatter = app_logging.FileFormatter


def __getattr__(name: str):  # pragma: no cover - compatibility shim
    if name == "CasinoCalendarFormatter":
        warnings.warn(
            "CasinoCalendarFormatter is deprecated; use casino_calendar.logging.app_logging.ConsoleFormatter",
            DeprecationWarning,
            stacklevel=2,
        )
        return app_logging.ConsoleFormatter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def setup_logger(name: str, log_file: Optional[str] = None, level: Optional[int] = None) -> logging.Logger:
    """Backward compatible wrapper for module-level loggers."""

    return setup_logging(name, log_file=log_file, level=level)


def setup_production_logger(name: str = "casino_calendar") -> logging.Logger:
    """Setup logger with production-ready log rotation and cleanup."""

    log_file_env = os.getenv("LOG_FILE")
    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    log_file = Path(log_file_env) if log_file_env else log_dir / "app.log"

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
            rotation_utils.normalise_archives(str(log_file), str(archive_directory))
        except Exception as exc:
            print(f"Warning: Could not process archive for {log_file}: {exc}")

    try:
        deleted_count = cleanup_old_logs(str(log_file.parent), 30)
        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} old log files")
    except Exception as exc:
        print(f"Warning: Could not clean up old logs: {exc}")

    level = get_log_level()
    logger = setup_logging(name, log_file=str(log_file), level=level)
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

    level = get_maintenance_log_level()
    log_path = get_maintenance_log_path()

    logger = setup_logging(
        name,
        log_file=str(log_path),
        level=level,
        maintenance=True,
        console_stream=sys.__stdout__,
    )
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


app_logger = setup_production_logger("casino_calendar")

app_logger.info("Logging system initialized")
app_logger.debug("Log level: %s", logging.getLevelName(get_log_level()))


__all__ = [
    "ContextLoggerAdapter",
    "ConsoleFormatter",
    "ENV_FILE",
    "FileFormatter",
    "app_logger",
    "cleanup_old_logs",
    "get_context_logger",
    "get_log_level",
    "get_maintenance_log_level",
    "get_maintenance_log_path",
    "log_dataframe_info",
    "log_function_call",
    "log_performance",
    "setup_logger",
    "setup_logging",
    "setup_maintenance_logger",
    "setup_production_logger",
    "setup_rotating_logger",
]
