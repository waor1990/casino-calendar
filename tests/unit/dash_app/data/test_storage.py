"""Tests for the event storage helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from casino_calendar.dash_app.data import EventRepository, EventStorage


def _build_sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "EventName": ["Sample Event"],
            "Casino": ["Example Casino"],
            "Location": ["123 Anywhere St"],
            "Offer": ["Free chips"],
            "StartDate": ["2025-01-01 00:00"],
            "EndDate": ["2025-01-02 23:59"],
        }
    )


def test_resolve_active_path_defaults_to_canonical(tmp_path: Path) -> None:
    base_dir = tmp_path / "raw"
    base_dir.mkdir()
    default_csv = base_dir / "casino_events.csv"
    default_csv.write_text(
        "EventName,StartDate,EndDate\\nOld,2024-01-01,2024-01-02\\n",
        encoding="utf-8",
    )

    storage = EventStorage(base_dir=base_dir)

    assert storage.resolve_active_path() == default_csv.resolve()


def test_save_events_update_overwrites_default_and_clears_metadata(
    tmp_path: Path,
) -> None:
    base_dir = tmp_path / "raw"
    base_dir.mkdir()
    default_csv = base_dir / "casino_events.csv"
    default_csv.write_text(
        "EventName,StartDate,EndDate\\nOld,2024-01-01,2024-01-02\\n",
        encoding="utf-8",
    )

    metadata_path = base_dir / "event_source.json"
    metadata_path.write_text(json.dumps({"path": "stale.csv"}), encoding="utf-8")

    storage = EventStorage(base_dir=base_dir)
    repository = EventRepository(storage=storage)
    df = _build_sample_frame()

    written_path = repository.save_events(df)

    assert written_path == default_csv.resolve()
    assert not metadata_path.exists()
    backup_files = list(base_dir.glob("casino_events.*.bak.csv"))
    assert len(backup_files) == 1
    csv_contents = default_csv.read_text(encoding="utf-8")
    assert "Sample Event" in csv_contents


def test_save_events_copy_records_override(tmp_path: Path) -> None:
    base_dir = tmp_path / "raw"
    base_dir.mkdir()
    storage = EventStorage(base_dir=base_dir)
    df = _build_sample_frame()

    written_path = storage.save_events(
        df,
        mode="copy",
        copy_filename="casino_events_override.csv",
        create_backup=False,
    )

    metadata_path = base_dir / "event_source.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert written_path.exists()
    assert metadata["path"] == str(written_path)
    assert storage.resolve_active_path() == written_path


def test_repository_uses_override_path(tmp_path: Path) -> None:
    base_dir = tmp_path / "raw"
    base_dir.mkdir()
    storage = EventStorage(base_dir=base_dir)

    df = _build_sample_frame()
    storage.save_events(
        df,
        mode="copy",
        copy_filename="casino_events_override.csv",
        create_backup=False,
    )

    repository = EventRepository(storage=storage)
    loaded = repository.load_events()

    assert list(loaded["EventName"]) == ["Sample Event"]
    assert storage.resolve_active_path().name == "casino_events_override.csv"


def test_timestamps_persist_after_save_and_reload(tmp_path: Path) -> None:
    """Verify that timestamps round-trip correctly through save/load cycles.

    When events are loaded, they are converted to naive UTC. When they are
    edited and saved, they must be converted back to PDT before writing to CSV.
    When reloaded, the to_naive_utc function should reconstruct the same
    timestamps, handling DST edges correctly.
    """
    base_dir = tmp_path / "raw"
    base_dir.mkdir()

    # Create initial CSV with naive timestamps in PDT
    # 2025-04-14 14:00 PDT (during PDT)
    initial_csv = base_dir / "casino_events.csv"
    initial_csv.write_text(
        "EventName,Casino,Location,Offer,StartDate,EndDate\n"
        "Spring Event,Test Casino,123 Main St,Free chips,"
        "2025-04-14 14:00,2025-04-14 15:00\n",
        encoding="utf-8",
    )

    # Load with EventRepository - this converts to naive UTC
    repository = EventRepository(EventStorage(base_dir=base_dir))
    loaded = repository.load_events()

    # Verify the loaded timestamps are in UTC
    assert pd.notna(loaded["StartDate"].iloc[0])
    original_start_utc = loaded["StartDate"].iloc[0]

    # Simulate editing - user receives PDT time, modifies it, returns as UTC
    # (since our in-memory representation is UTC)
    modified = loaded.copy()
    modified["EventName"] = ["Spring Event - Modified"]
    # Keep timestamps as-is (they're still UTC)

    # Save the modified events back
    storage = EventStorage(base_dir=base_dir)
    storage.save_events(modified, mode="update", create_backup=False)

    # Reload the events
    reloaded = repository.load_events()

    # The reloaded UTC timestamp should match the original UTC timestamp
    reloaded_start_utc = reloaded["StartDate"].iloc[0]
    assert (
        original_start_utc == reloaded_start_utc
    ), f"Timestamps diverged: {original_start_utc} != {reloaded_start_utc}"
    assert reloaded["EventName"].iloc[0] == "Spring Event - Modified"


def test_repository_save_events_delegates_to_storage() -> None:
    class _SpyStorage:
        def __init__(self) -> None:
            self.last_df: pd.DataFrame | None = None
            self.kwargs: dict[str, Any] | None = None

        def resolve_active_path(self) -> Path:
            return Path("casino_events.csv")

        def save_events(
            self,
            df: pd.DataFrame,
            *,
            mode: str = "update",
            copy_filename: str | None = None,
            create_backup: bool = True,
        ) -> Path:
            self.last_df = df.copy()
            self.kwargs = {
                "mode": mode,
                "copy_filename": copy_filename,
                "create_backup": create_backup,
            }
            return Path("casino_events.csv")

    storage = _SpyStorage()
    repository = EventRepository(storage=storage)
    df = _build_sample_frame()

    saved_path = repository.save_events(df)

    assert saved_path == Path("casino_events.csv")
    pd.testing.assert_frame_equal(storage.last_df, df)
    assert storage.kwargs == {
        "mode": "update",
        "copy_filename": None,
        "create_backup": True,
    }
