"""Central logging configuration for the Casino Calendar application."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()  # This loads the .env file automatically
except ImportError:
    # python-dotenv not installed, continue without it
    pass

# Import our custom log rotation utilities
try:
    from utils.log_rotation import setup_rotating_logger, cleanup_old_logs
except ImportError:
    # Fallback if utils module not available
    setup_rotating_logger = None
    cleanup_old_logs = None


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


def get_log_level() -> int:
    """Get log level from environment variable or default to INFO."""
    level_str = os.getenv("LOG_LEVEL", "INFO").upper()

    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    return level_map.get(level_str, logging.INFO)


def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Setup and configure a logger with console and optional file output.

    Args:
        name: Logger name (typically __name__)
        log_file: Optional file path for log output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    logger.setLevel(get_log_level())

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(get_log_level())
    console_handler.setFormatter(CasinoCalendarFormatter(use_colors=True))
    logger.addHandler(console_handler)

    # File handler - use log_file parameter or fall back to LOG_FILE env var
    file_path = log_file or os.getenv("LOG_FILE")
    if file_path:
        log_path = Path(file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Use larger rotation settings for development
        max_bytes = 10 * 1024 * 1024  # 10MB per file
        backup_count = 5  # Keep 5 backup files

        file_handler = RotatingFileHandler(
            file_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)  # File gets all levels
        file_handler.setFormatter(CasinoCalendarFormatter(use_colors=False))
        logger.addHandler(file_handler)

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
    # Get log file from environment variable, fallback to default
    log_file_env = os.getenv("LOG_FILE")
    if not log_file_env:
        log_dir = Path("logs")
        log_file = log_dir / "casino_calendar.log"
    else:
        log_file = Path(log_file_env)

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Clean up old logs (keep last 30 days)
    if cleanup_old_logs:
        try:
            deleted_count = cleanup_old_logs(str(log_file.parent), days_to_keep=30)
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} old log files")
        except Exception as e:
            print(f"Warning: Could not clean up old logs: {e}")

    # Use custom rotating logger if available, otherwise fallback
    if setup_rotating_logger:
        logger = setup_rotating_logger(
            name=name,
            log_file=str(log_file),
            level=logging.INFO,  # Production level
            max_bytes=10 * 1024 * 1024,  # 10MB
            backup_count=5,
            console_output=True,
        )
        logger.info("Production logging initialized with rotation")
    else:
        # Fallback to standard setup
        logger = setup_logger(name, str(log_file))
        logger.info("Standard logging initialized")

    return logger


def log_function_call(logger: logging.Logger, func_name: str, **kwargs):
    """Log function call with parameters (for debugging)."""
    params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug(f"Calling {func_name}({params})")


def log_performance(
    logger: logging.Logger, operation: str, start_time: float, end_time: float
):
    """Log performance metrics for operations."""
    duration = end_time - start_time
    logger.info(f"Performance: {operation} completed in {duration:.3f}s")


def log_dataframe_info(logger: logging.Logger, df, description: str = "DataFrame"):
    """Log useful information about a pandas DataFrame."""
    if df is not None and hasattr(df, "shape"):
        logger.debug(f"{description} shape: {df.shape}, columns: {list(df.columns)}")
    else:
        logger.warning(f"{description} is None or invalid")


# Global application logger instance - use production setup
app_logger = setup_production_logger("casino_calendar")

# Log startup
app_logger.info("Logging system initialized")
app_logger.debug(f"Log level set to: {logging.getLevelName(get_log_level())}")
