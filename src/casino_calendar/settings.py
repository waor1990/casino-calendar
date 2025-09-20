"""Global configuration and environment helpers for Casino Calendar."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Final

from pytz import UTC, timezone

try:  # Optional dependency loaded lazily
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback when python-dotenv missing
    load_dotenv = None  # type: ignore[assignment]

# Resolve important filesystem locations early so other modules can import them
PACKAGE_DIR: Final[Path] = Path(__file__).resolve().parent
SRC_DIR: Final[Path] = PACKAGE_DIR.parent
PROJECT_ROOT: Final[Path] = SRC_DIR.parent
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
ENV_FILE: Final[Path] = PROJECT_ROOT / ".env"

if load_dotenv is not None:
    # Load environment variables once so downstream modules do not have to.
    load_dotenv(dotenv_path=ENV_FILE, override=False)

# Timezone configuration shared across the app
APP_TIMEZONE = timezone(os.getenv("APP_TIMEZONE", "America/Los_Angeles"))
UTC_TZ = UTC


@lru_cache(maxsize=None)
def get_env(key: str, default: str | None = None) -> str | None:
    """Return environment variable key with default fallback."""

    return os.getenv(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """Return boolean interpretation of environment variable key."""

    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def get_env_int(key: str, default: int) -> int:
    """Return integer environment variable with fallback."""

    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


__all__ = [
    "APP_TIMEZONE",
    "DATA_DIR",
    "ENV_FILE",
    "PACKAGE_DIR",
    "PROJECT_ROOT",
    "SRC_DIR",
    "UTC_TZ",
    "get_env",
    "get_env_bool",
    "get_env_int",
]
