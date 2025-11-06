"""Repository helpers wrapping event data access."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Protocol

import pandas as pd

from casino_calendar.settings import DATA_DIR

from .loader import load_event_data
from ..services.layout_state import to_pdt


class SupportsEvents(Protocol):
    """Protocol describing objects that can return a DataFrame of events."""

    def load_events(self) -> pd.DataFrame:
        """Return event data."""


class EventRepository:
    """Repository responsible for loading event data from disk."""

    def __init__(self, csv_path: Path | None = None) -> None:
        self._csv_path = csv_path or DATA_DIR / "raw" / "casino_events.csv"

    def load_events(self) -> pd.DataFrame:
        """Return the event data set."""

        return load_event_data(self._csv_path)

    def save_events(self, df: pd.DataFrame) -> Path:
        """Persist ``df`` to disk, creating a backup of the previous file."""

        self._csv_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._csv_path.with_suffix(self._csv_path.suffix + ".tmp")
        backup_path = self._csv_path.with_suffix(self._csv_path.suffix + ".bak")

        persisted = df.copy()
        for column in ["StartDate", "EndDate"]:
            if column in persisted.columns:
                persisted[column] = (
                    pd.to_datetime(persisted[column], errors="coerce")
                    .apply(
                        lambda ts: to_pdt(ts).isoformat(timespec="minutes")
                        if pd.notna(ts)
                        else ""
                    )
                )

        persisted.to_csv(temp_path, index=False)

        if self._csv_path.exists():
            shutil.copy2(self._csv_path, backup_path)

        temp_path.replace(self._csv_path)
        return self._csv_path


__all__ = ["EventRepository", "SupportsEvents"]
