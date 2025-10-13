import importlib.util
import sys
from pathlib import Path
from unittest import mock

import pytest

MODULE_PATH = Path(__file__).resolve().parents[3] / "src" / "casino_calendar" / "logging" / "rotation.py"
spec = importlib.util.spec_from_file_location("rotation_under_test", MODULE_PATH)
rotation = importlib.util.module_from_spec(spec)
sys.modules["rotation_under_test"] = rotation
assert spec.loader is not None
spec.loader.exec_module(rotation)

_replace_with_retry = rotation._replace_with_retry


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
