"""Repository helpers wrapping event data access."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import pandas as pd

from .loader import load_event_data
from .storage import EventStorage


class SupportsEvents(Protocol):
    """Protocol describing objects that can return a DataFrame of events."""

    def load_events(self) -> pd.DataFrame:
        """Return event data."""


class EventRepository:
    """Load and persist event data while delegating storage concerns to EventStorage."""

    def __init__(self, storage: EventStorage | None = None) -> None:
        self._storage = storage or EventStorage()

    def load_events(self) -> pd.DataFrame:
        """Return the event data set using the active storage path."""

        csv_path = self._storage.resolve_active_path()
        return load_event_data(csv_path)

    def save_events(self, df: pd.DataFrame) -> Path:
        """Persist ``df`` via EventStorage with backup creation enabled."""

        return self._storage.save_events(df, mode="update", create_backup=True)


__all__ = ["EventRepository", "SupportsEvents"]
