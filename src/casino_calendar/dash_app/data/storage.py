"""Utilities for persisting edits to the event data set."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd
from casino_calendar.logging.config import setup_logger
from casino_calendar.settings import APP_TIMEZONE, DATA_DIR, UTC_TZ

logger = setup_logger(__name__)

_METADATA_FILENAME = "event_source.json"


def _to_local_timezone(
    timestamp: pd.Timestamp | str,
) -> pd.Timestamp | str:
    """Convert from naive UTC to naive local timezone for persistence.

    This is the inverse of the to_naive_utc transform in the loader.
    When events are saved to CSV, timestamps must be converted from UTC
    back to the configured local timezone (PDT) so that when reloaded,
    the to_naive_utc function properly reconstructs the original times.

    Parameters
    ----------
    timestamp:
        A pandas Timestamp or string (assumed to be in naive UTC if a
        Timestamp). Strings are returned unchanged.

    Returns
    -------
    A pandas Timestamp in naive local time or the original string if input
    was string.
    """
    # If input is already a string, return as-is (not yet parsed as Timestamp)
    if isinstance(timestamp, str):
        return timestamp

    if pd.isna(timestamp):
        return timestamp

    if timestamp.tzinfo is None:
        aware_utc = timestamp.replace(tzinfo=UTC_TZ)
    else:
        aware_utc = timestamp

    local_aware = aware_utc.astimezone(APP_TIMEZONE)
    return pd.Timestamp(local_aware.replace(tzinfo=None))


class EventStorage:
    """Manage reading and writing the casino event CSV file."""

    def __init__(
        self,
        base_dir: Path | None = None,
        default_filename: str = "casino_events.csv",
        metadata_filename: str = _METADATA_FILENAME,
    ) -> None:
        self._base_dir = (base_dir or DATA_DIR / "raw").resolve()
        self._default_filename = default_filename
        self._default_csv = (self._base_dir / default_filename).resolve()
        self._metadata_path = (self._base_dir / metadata_filename).resolve()

    @property
    def default_csv(self) -> Path:
        """Return the canonical CSV path."""

        return self._default_csv

    def resolve_active_path(self) -> Path:
        """Return the path that should currently be used for loading events."""

        metadata_path = self._read_metadata_path()
        if metadata_path and metadata_path.exists():
            logger.debug("Resolved override event path: %s", metadata_path)
            return metadata_path

        logger.debug("Using default event CSV: %s", self._default_csv)
        return self._default_csv

    def save_events(
        self,
        df: pd.DataFrame,
        *,
        mode: Literal["update", "copy"] = "update",
        copy_filename: str | None = None,
        create_backup: bool = True,
    ) -> Path:
        """Persist event data and return the written path.

        Parameters
        ----------
        df:
            DataFrame containing the latest event information. Date columns
            (StartDate, EndDate) are assumed to be in naive UTC and will be
            converted to the local timezone before writing to CSV.
        mode:
            ``"update"`` writes directly to the canonical CSV. ``"copy"``
            creates a new CSV file and records it so future loads use the copy.
        copy_filename:
            Optional filename for copy mode. Defaults to a timestamped file.
        create_backup:
            Whether to create a timestamped ``.bak`` copy before overwriting a
            file that already exists.
        """

        if mode not in {"update", "copy"}:
            msg = f"Invalid persistence mode: {mode}"
            raise ValueError(msg)

        # Convert timestamps from UTC to local timezone before writing
        df_to_write = df.copy()
        for column in ["StartDate", "EndDate"]:
            if column in df_to_write.columns:
                df_to_write[column] = df_to_write[column].map(_to_local_timezone)

        target = self._resolve_target_path(
            mode=mode,
            copy_filename=copy_filename,
        )
        target.parent.mkdir(parents=True, exist_ok=True)

        if create_backup and target.exists():
            backup_path = self._build_backup_path(target)
            logger.debug("Creating backup %s", backup_path)
            backup_path.write_bytes(target.read_bytes())

        logger.info("Writing events to %s", target)
        df_to_write.to_csv(target, index=False)

        if mode == "copy":
            self._write_metadata_path(target)
        else:
            self._clear_metadata_path()

        return target

    # Internal helpers -------------------------------------------------

    def _read_metadata_path(self) -> Path | None:
        try:
            data = json.loads(self._metadata_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            logger.warning(
                "Unable to parse event metadata file %s: %s",
                self._metadata_path,
                exc,
            )
            return None

        raw_path = data.get("path")
        if not raw_path:
            return None

        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = (self._base_dir / candidate).resolve()

        return candidate

    def _write_metadata_path(self, path: Path) -> None:
        metadata = {"path": str(path)}
        payload = json.dumps(metadata, indent=2)
        self._metadata_path.write_text(
            f"{payload}\n",
            encoding="utf-8",
        )
        logger.debug("Updated event metadata to point at %s", path)

    def _clear_metadata_path(self) -> None:
        try:
            self._metadata_path.unlink()
            logger.debug("Cleared event metadata override")
        except FileNotFoundError:
            logger.debug("No event metadata override to clear")

    def _resolve_target_path(
        self,
        *,
        mode: Literal["update", "copy"],
        copy_filename: str | None,
    ) -> Path:
        if mode == "update":
            return self._default_csv

        filename = copy_filename or self._generate_copy_filename()
        return (self._base_dir / filename).resolve()

    @staticmethod
    def _build_backup_path(target: Path) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_name = f"{target.stem}.{timestamp}.bak{target.suffix}"
        return target.with_name(backup_name)

    @staticmethod
    def _generate_copy_filename() -> str:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"casino_events_{timestamp}.csv"


__all__ = ["EventStorage"]
