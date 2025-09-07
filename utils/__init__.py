"""
Utilities package initializer.

This module avoids eager imports of submodules to prevent side effects during
package import (e.g., logging configuration). It provides lazy access to common
submodules so statements like `from utils import data_parsing` continue to work
without importing everything at package import time.
"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = [
    "colors",
    "config_cache",
    "data_parsing",
    "log_rotation",
]


def __getattr__(name: str) -> Any:  # PEP 562 lazy attribute import
    if name in {
        "colors",
        "config_cache",
        "data_parsing",
        "log_rotation",
    }:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
