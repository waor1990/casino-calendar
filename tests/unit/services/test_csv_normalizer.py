import csv
from pathlib import Path

import pytest

from casino_calendar.services import csv_normalizer
from casino_calendar.services.csv_normalizer import normalize_csv


def _write_rows(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerows(rows)


def _read_dicts(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def test_normalize_csv_preserves_existing_layout(tmp_path: Path) -> None:
    input_path = tmp_path / "events.csv"
    rows = [
        ["EventName", "Casino", "Location", "Offer", "StartDate", "EndDate"],
        [
            "Event A",
            "Casino A",
            "Main Hall",
            "Promo",
            "7/1/2025 10:00",
            "7/1/2025 12:00",
        ],
    ]
    _write_rows(input_path, rows)

    result = normalize_csv(input_path, input_path)
    assert result.rows_written == 1
    assert result.skipped_rows == 0

    data = _read_dicts(input_path)
    assert data == [
        {
            "EventName": "Event A",
            "Casino": "Casino A",
            "Location": "Main Hall",
            "Offer": "Promo",
            "StartDate": "7/1/2025 10:00",
            "EndDate": "7/1/2025 12:00",
        }
    ]


def test_normalize_csv_combines_columns(tmp_path: Path) -> None:
    input_path = tmp_path / "raw.csv"
    output_path = tmp_path / "normalized.csv"
    rows = [
        [
            "Event Title",
            "Casino Name",
            "Address",
            "City",
            "State",
            "Details",
            "Start Date",
            "Start Time",
            "End Date",
            "End Time",
        ],
        [
            "Mega Drawing",
            "Tulalip Resort",
            "10200 Quil Ceda Blvd",
            "Marysville",
            "WA",
            "Win big prizes",
            "08/15/2025",
            "8:00 PM",
            "08/16/2025",
            "1:00 AM",
        ],
    ]
    _write_rows(input_path, rows)

    result = normalize_csv(input_path, output_path)
    assert result.rows_written == 1

    data = _read_dicts(output_path)
    assert data[0] == {
        "EventName": "Mega Drawing",
        "Casino": "Tulalip Resort",
        "Location": "10200 Quil Ceda Blvd, Marysville, WA",
        "Offer": "Win big prizes",
        "StartDate": "8/15/2025 20:00",
        "EndDate": "8/16/2025 1:00",
    }


def test_normalize_csv_defaults_missing_end_time(tmp_path: Path) -> None:
    input_path = tmp_path / "missing_end_time.csv"
    output_path = tmp_path / "normalized.csv"
    rows = [
        [
            "Event",
            "Casino",
            "Location",
            "Offer",
            "Start Date",
            "Start Time",
            "End Date",
        ],
        [
            "Late Night Party",
            "Lucky Star",
            "Sky Lounge",
            "DJ and prizes",
            "09/10/2025",
            "9:00 PM",
            "09/10/2025",
        ],
    ]
    _write_rows(input_path, rows)

    result = normalize_csv(input_path, output_path)
    assert result.rows_written == 1
    assert any("defaulting to 23:59" in warning for warning in result.warnings)

    data = _read_dicts(output_path)
    assert data[0]["EndDate"] == "9/10/2025 23:59"


def test_find_candidate_csv_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    status_output = (
        "?? data/raw/new_file.csv\n M data/raw/casino_events.csv\n?? docs/readme.txt\n"
    )

    class DummyCompletedProcess:
        def __init__(self, stdout: str) -> None:
            self.stdout = stdout
            self.returncode = 0
            self.stderr = ""

    def fake_run(*args, **kwargs):
        return DummyCompletedProcess(status_output)

    monkeypatch.setattr(csv_normalizer.subprocess, "run", fake_run)

    candidates = csv_normalizer.find_candidate_csv_paths()
    assert candidates == [
        Path("data/raw/new_file.csv"),
        Path("data/raw/casino_events.csv"),
    ]
