import datetime
import importlib.util
import sys
from pathlib import Path
from unittest import mock

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "casino_calendar"
    / "logging"
    / "rotation.py"
)
spec = importlib.util.spec_from_file_location("rotation_under_test", MODULE_PATH)
rotation = importlib.util.module_from_spec(spec)
sys.modules["rotation_under_test"] = rotation
assert spec.loader is not None
spec.loader.exec_module(rotation)

_replace_with_retry = rotation._replace_with_retry
_write_lines_with_fallback = rotation._write_lines_with_fallback


def _line(year: int, month: int, day: int, message: str) -> str:
    return f"{year:04d}-{month:02d}-{day:02d} 10:00:00 | INFO     | test.module       | {message}\n"


class FrozenDateTime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):  # type: ignore[override]
        return cls(2025, 9, 30, 12, 0, 0, tzinfo=tz)


def test_replace_with_retry_success():
    src = mock.Mock()
    dest = Path("dest.log")

    src.replace.return_value = dest

    _replace_with_retry(src, dest)

    src.replace.assert_called_once_with(dest)


def test_replace_with_retry_recovers_after_permission_error():
    src = mock.Mock()
    dest = Path("dest.log")

    src.replace.side_effect = [PermissionError("locked"), dest]

    with mock.patch.object(rotation.time, "sleep") as sleep_mock:
        _replace_with_retry(src, dest)

    assert src.replace.call_count == 2
    sleep_mock.assert_called_once()


def test_replace_with_retry_raises_after_exhausting_attempts():
    src = mock.Mock()
    dest = Path("dest.log")

    src.replace.side_effect = PermissionError("still locked")

    with mock.patch.object(rotation.time, "sleep"):
        with pytest.raises(PermissionError):
            _replace_with_retry(src, dest, attempts=3, delay=0)

    assert src.replace.call_count == 3


def test_write_lines_with_fallback_replaces_file(tmp_path):
    dest = tmp_path / "casino_calendar.log"
    dest.write_text("old\n", encoding="utf-8")

    _write_lines_with_fallback(dest, ["new\n", "line\n"])

    assert dest.read_text(encoding="utf-8") == "new\nline\n"
    assert not dest.with_suffix(dest.suffix + ".tmp").exists()


def test_write_lines_with_fallback_recovers_from_permission_error(
    monkeypatch, tmp_path
):
    dest = tmp_path / "casino_calendar.log"
    dest.write_text("old\n", encoding="utf-8")

    monkeypatch.setattr(
        rotation,
        "_replace_with_retry",
        mock.Mock(side_effect=PermissionError("locked")),
    )

    _write_lines_with_fallback(dest, ["new\n"])

    assert dest.read_text(encoding="utf-8") == "new\n"
    assert not dest.with_suffix(dest.suffix + ".tmp").exists()


def test_archive_and_trim_by_month_creates_monthly_files(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    archive_dir = log_dir / "archive"
    archive_dir.mkdir(parents=True)
    log_file = log_dir / "casino_calendar_prod.log"
    log_file.write_text(
        "".join(
            [
                _line(2025, 8, 15, "august-one"),
                _line(2025, 8, 20, "august-two"),
                _line(2025, 9, 5, "sept-one"),
                _line(2025, 9, 6, "sept-two"),
                _line(2025, 10, 12, "only-oct-12"),
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(rotation, "datetime", FrozenDateTime)

    summary = rotation.archive_and_trim_by_month(
        str(log_file), archive_dir=str(archive_dir)
    )

    active_content = log_file.read_text(encoding="utf-8")
    assert "sept-one" in active_content
    assert "sept-two" in active_content
    assert "august-one" not in active_content

    august_file = archive_dir / "casino_calendar_prod_2025-08.log"
    assert august_file.exists()
    august_content = august_file.read_text(encoding="utf-8")
    assert "august-one" in august_content
    assert "august-two" in august_content

    oct_file = archive_dir / "casino_calendar_prod_2025-10.log"
    assert not oct_file.exists()

    all_file = archive_dir / "casino_calendar_prod_all.log"
    assert all_file.exists()
    assert "august-one" in all_file.read_text(encoding="utf-8")
    assert "only-oct-12" not in all_file.read_text(encoding="utf-8")

    assert summary["archived_lines"] == 2


def test_copy_lines_by_days_copies_without_trimming(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    archive_dir = log_dir / "archive"
    archive_dir.mkdir(parents=True)
    log_file = log_dir / "casino_calendar_prod.log"
    log_file.write_text(
        "".join(
            [
                _line(2025, 8, 10, "older"),
                _line(2025, 9, 1, "recent"),
            ]
        ),
        encoding="utf-8",
    )

    fake_now = datetime.datetime(2025, 9, 30, 12, 0, 0)
    monkeypatch.setattr(rotation.time, "time", lambda: fake_now.timestamp())

    summary = rotation.copy_lines_by_days(
        str(log_file), 30, archive_dir=str(archive_dir)
    )

    assert summary["copied_lines"] == 1
    august_file = archive_dir / "casino_calendar_prod_2025-08.log"
    assert august_file.exists()
    assert "older" in august_file.read_text(encoding="utf-8")

    content = log_file.read_text(encoding="utf-8")
    assert "older" in content  # copy-only, not trimmed


def test_copy_current_log_preserves_active_file(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    archive_dir = log_dir / "archive"
    archive_dir.mkdir(parents=True)
    log_file = log_dir / "casino_calendar_prod.log"
    log_file.write_text(
        "".join(
            [
                _line(2025, 9, 5, "active-one"),
                _line(2025, 9, 6, "active-two"),
            ]
        ),
        encoding="utf-8",
    )

    rotation.copy_current_log(str(log_file), archive_dir=str(archive_dir))

    # Active file still exists with content
    assert log_file.exists()
    active_content = log_file.read_text(encoding="utf-8")
    assert "active-one" in active_content

    # Archive should contain copied data
    all_file = archive_dir / "casino_calendar_prod_all.log"
    assert all_file.exists()
    all_content = all_file.read_text(encoding="utf-8")
    assert "active-one" in all_content
