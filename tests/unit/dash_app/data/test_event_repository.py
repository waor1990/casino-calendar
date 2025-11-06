from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd

from casino_calendar.dash_app.data import loader
from casino_calendar.dash_app.data.repositories import EventRepository
from casino_calendar.settings import APP_TIMEZONE


def _write_csv(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_resolve_active_csv_path_prefers_newer_edited_file(tmp_path: Path) -> None:
    base = tmp_path / "casino_events.csv"
    edited = tmp_path / "casino_events.edited.csv"

    _write_csv(base, "EventName\nOriginal\n")
    _write_csv(edited, "EventName\nEdited\n")

    now = time.time()
    os.utime(base, (now - 120, now - 120))
    os.utime(edited, (now, now))

    resolved = loader.resolve_active_csv_path(base)
    assert resolved == edited


def test_save_event_data_updates_primary_and_removes_edited(tmp_path: Path) -> None:
    base = tmp_path / "casino_events.csv"
    edited = tmp_path / "casino_events.edited.csv"

    _write_csv(base, "EventName,StartDate,EndDate\nOriginal,2024-01-01,2024-01-02\n")
    _write_csv(edited, "EventName,StartDate,EndDate\nOld,2024-01-01,2024-01-02\n")

    df = pd.DataFrame(
        [
            {
                "EventName": "Updated",
                "StartDate": "2025-07-01 00:00",
                "EndDate": "2025-07-02 12:00",
            }
        ]
    )

    written_path = loader.save_event_data(df, base)
    assert written_path == base
    assert not edited.exists()

    persisted = pd.read_csv(base)
    assert list(persisted["EventName"]) == ["Updated"]


def test_save_event_data_converts_utc_to_local(tmp_path: Path) -> None:
    base = tmp_path / "casino_events.csv"
    _write_csv(base, "EventName,StartDate,EndDate\nSeed,2024-01-01,2024-01-02\n")

    df = pd.DataFrame(
        [
            {
                "EventName": "Shifted",
                "StartDate": "2025-07-01 14:00:00",
                "EndDate": "2025-07-01 20:30:00",
            }
        ]
    )

    loader.save_event_data(df, base)

    persisted = pd.read_csv(base)
    start_value = pd.Timestamp("2025-07-01 14:00:00", tz="UTC").tz_convert(APP_TIMEZONE)
    end_value = pd.Timestamp("2025-07-01 20:30:00", tz="UTC").tz_convert(APP_TIMEZONE)

    assert persisted.loc[0, "StartDate"] == start_value.tz_localize(None).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    assert persisted.loc[0, "EndDate"] == end_value.tz_localize(None).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def test_save_event_data_uses_fallback_when_primary_write_fails(
    monkeypatch, tmp_path: Path
) -> None:
    base = tmp_path / "casino_events.csv"
    fallback = tmp_path / "casino_events.edited.csv"

    _write_csv(base, "EventName\nOriginal\n")

    df = pd.DataFrame(
        [
            {
                "EventName": "Fallback",
                "StartDate": "2025-08-01",
                "EndDate": "2025-08-02",
            }
        ]
    )

    original_writer = loader._write_dataframe_atomic

    def failing_writer(dataframe: pd.DataFrame, target: Path) -> None:  # type: ignore[override]
        if target == base:
            raise OSError("Permission denied")
        original_writer(dataframe, target)

    monkeypatch.setattr(loader, "_write_dataframe_atomic", failing_writer)

    written_path = loader.save_event_data(df, base)
    assert written_path == fallback
    assert fallback.exists()

    persisted = pd.read_csv(fallback)
    assert list(persisted["EventName"]) == ["Fallback"]


def test_event_repository_drops_internal_columns(tmp_path: Path) -> None:
    base = tmp_path / "casino_events.csv"
    _write_csv(base, "EventName,StartDate,EndDate\nSeed,2024-01-01,2024-01-02\n")

    repository = EventRepository(csv_path=base)
    df = pd.DataFrame(
        [
            {
                "EventName": "Updated",
                "StartDate": "2025-09-01",
                "EndDate": "2025-09-02",
                "_row_index": 7,
            }
        ]
    )

    repository.save_events(df)
    persisted = pd.read_csv(base)

    assert "_row_index" not in persisted.columns
    assert list(persisted["EventName"]) == ["Updated"]
