"""Repository helpers wrapping event data access.

CSV-based repositories are retained for backward compatibility but the
REST API-backed ``APIEventRepository`` should be used for new work.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import pandas as pd

from casino_calendar.settings import DATA_DIR

from .api_repository import APIEventRepository
from .loader import load_event_data


class SupportsEvents(Protocol):
    """Protocol describing objects that can return a DataFrame of events."""

    def load_events(self) -> pd.DataFrame:
        """Return event data."""


class EventRepository:
    """Legacy repository responsible for loading CSV-based event data.

    This class is kept for tooling compatibility; the Dash app now
    consumes events via :class:`APIEventRepository`.
    """

    def __init__(self, csv_path: Path | None = None) -> None:
        self._csv_path = csv_path or DATA_DIR / "raw" / "casino_events.csv"

    def load_events(self) -> pd.DataFrame:
        """Return the event data set from CSV."""

        return load_event_data(self._csv_path)


__all__ = ["APIEventRepository", "EventRepository", "SupportsEvents"]
