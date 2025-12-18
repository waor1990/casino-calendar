"""Repository helpers wrapping event data access."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import pandas as pd

from casino_calendar.settings import DATA_DIR

from .loader import load_event_data


class SupportsEvents(Protocol):
    """Protocol describing objects that can return a DataFrame of events."""

    def load_events(self) -> pd.DataFrame:
        """Return event data."""
        ...


class EventRepository:
    """Repository responsible for loading event data from disk."""

    def __init__(self, csv_path: Path | None = None) -> None:
        self._csv_path = csv_path or DATA_DIR / "raw" / "casino_events.csv"

    def load_events(self) -> pd.DataFrame:
        """Return the event data set."""

        return load_event_data(self._csv_path)


__all__ = ["EventRepository", "SupportsEvents"]
