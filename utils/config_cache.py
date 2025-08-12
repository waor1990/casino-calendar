"""Centralized configuration caching utilities.

Provides a simple JSON configuration cache to avoid repeated
file reads for static configuration data.  The cache can be
cleared by setting the environment variable ``CONFIG_CACHE_BUST``
to any non-empty value.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

from app_components.logging_config import setup_logger

# Initialize module logger
logger = setup_logger(__name__)

# Module level cache storage
_CACHE: Dict[str, Any] = {}

# Directory containing configuration files
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def get_config(filename: str, *, bust_cache: bool = False) -> Any:
    """Return the parsed contents of a JSON configuration file.

    The file is read from :mod:`data` on first access and the result is
    cached for subsequent calls.  Set the ``CONFIG_CACHE_BUST``
    environment variable or use bust_cache=True to force a reload.

    Args:
        filename: Name of the JSON file in the data directory
        bust_cache: If True, force reload even if cached

    Returns:
        Parsed JSON data or None if file not found/invalid
    """

    # Check for cache busting - either via env var or parameter
    if bust_cache or os.getenv("CONFIG_CACHE_BUST"):
        if filename in _CACHE:
            logger.debug("Cache busting - removing %s from cache", filename)
            _CACHE.pop(filename, None)

    if filename in _CACHE:
        return _CACHE[filename]

    path = DATA_DIR / filename
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        _CACHE[filename] = data
        logger.debug("Loaded configuration %s", filename)
        return data
    except FileNotFoundError:
        logger.error("Configuration file not found: %s", path)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in %s: %s", path, e, exc_info=True)

    # Cache empty fallback to avoid repeated file I/O on failure
    _CACHE[filename] = None
    return None


def clear_cache() -> None:
    """Clear all cached configuration data."""
    _CACHE.clear()
    logger.debug("Configuration cache cleared")


def warm_cache(*filenames: str) -> None:
    """Preload multiple configuration files into cache.

    Args:
        *filenames: Configuration file names to preload
    """
    for filename in filenames:
        get_config(filename)
    logger.debug("Warmed cache with %d configuration files", len(filenames))
