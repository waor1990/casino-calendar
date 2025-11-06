"""Repository helpers wrapping event data access."""

from __future__ import annotations

from typing import Protocol

import pandas as pd

from .loader import load_event_data
from .storage import EventStorage


class SupportsEvents(Protocol):
    """Protocol describing objects that can return a DataFrame of events."""

    def load_events(self) -> pd.DataFrame:
        """Return event data."""


class EventRepository:
    """Repository responsible for loading event data from disk."""

    def __init__(self, storage: EventStorage | None = None) -> None:
        self._storage = storage or EventStorage()

    def load_events(self) -> pd.DataFrame:
        """Return the event data set."""

        csv_path = self._storage.resolve_active_path()
        return load_event_data(csv_path)


__all__ = ["EventRepository", "SupportsEvents"]
