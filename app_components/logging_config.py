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

        file_handler = RotatingFileHandler(
            file_path, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        file_handler.setLevel(logging.DEBUG)  # File gets all levels
        file_handler.setFormatter(CasinoCalendarFormatter(use_colors=False))
        logger.addHandler(file_handler)

    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False

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


# Global application logger instance
app_logger = setup_logger(
    "casino_calendar",
    log_file=os.getenv("LOG_FILE"),  # Optional file logging via env var
)

# Log startup
app_logger.info("Logging system initialized")
app_logger.debug(f"Log level set to: {logging.getLevelName(get_log_level())}")
