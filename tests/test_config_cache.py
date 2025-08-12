import importlib
import json
import sys
from pathlib import Path

UTILS_DIR = Path(__file__).resolve().parents[1] / "utils"
sys.path.insert(0, str(UTILS_DIR))
config_cache = importlib.import_module("config_cache")


def test_get_config_caches(tmp_path, monkeypatch):
    config_cache._CACHE.clear()
    monkeypatch.setattr(config_cache, "DATA_DIR", tmp_path)
    config_file = tmp_path / "sample.json"
    config_file.write_text(json.dumps({"a": 1}), encoding="utf-8")

    first = config_cache.get_config("sample.json")
    config_file.write_text(json.dumps({"a": 2}), encoding="utf-8")
    second = config_cache.get_config("sample.json")

    assert first == {"a": 1}
    assert second == {"a": 1}


def test_get_config_cache_bust(tmp_path, monkeypatch):
    config_cache._CACHE.clear()
    monkeypatch.setattr(config_cache, "DATA_DIR", tmp_path)
    config_file = tmp_path / "sample.json"
    config_file.write_text(json.dumps({"a": 1}), encoding="utf-8")

    first = config_cache.get_config("sample.json")
    config_file.write_text(json.dumps({"a": 2}), encoding="utf-8")
    monkeypatch.setenv("CONFIG_CACHE_BUST", "1")
    second = config_cache.get_config("sample.json")

    assert first == {"a": 1}
    assert second == {"a": 2}
