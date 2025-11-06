"""Tests for the event storage helpers."""
from __future__ import annotations

import json
from pathlib import Path

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

    storage = EventStorage(base_dir=base_dir)
    df = _build_sample_frame()

    written_path = storage.save_events(df, mode="update")

    assert written_path == default_csv.resolve()
    assert not (base_dir / "event_source.json").exists()
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
