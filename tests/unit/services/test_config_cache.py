import json

from casino_calendar.services import config_cache


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


def test_get_config_cache_bust_env_var(tmp_path, monkeypatch):
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


def test_get_config_cache_bust_parameter(tmp_path, monkeypatch):
    config_cache._CACHE.clear()
    monkeypatch.setattr(config_cache, "DATA_DIR", tmp_path)
    config_file = tmp_path / "sample.json"
    config_file.write_text(json.dumps({"a": 1}), encoding="utf-8")

    first = config_cache.get_config("sample.json")
    config_file.write_text(json.dumps({"a": 2}), encoding="utf-8")
    second = config_cache.get_config("sample.json", bust_cache=True)

    assert first == {"a": 1}
    assert second == {"a": 2}


def test_clear_cache(tmp_path, monkeypatch):
    config_cache._CACHE.clear()
    monkeypatch.setattr(config_cache, "DATA_DIR", tmp_path)
    config_file = tmp_path / "sample.json"
    config_file.write_text(json.dumps({"test": "data"}), encoding="utf-8")

    # Load and cache the file
    config_cache.get_config("sample.json")
    assert len(config_cache._CACHE) == 1

    # Clear cache
    config_cache.clear_cache()
    assert len(config_cache._CACHE) == 0


def test_warm_cache(tmp_path, monkeypatch):
    config_cache._CACHE.clear()
    monkeypatch.setattr(config_cache, "DATA_DIR", tmp_path)

    # Create test files
    (tmp_path / "file1.json").write_text(json.dumps({"a": 1}), encoding="utf-8")
    (tmp_path / "file2.json").write_text(json.dumps({"b": 2}), encoding="utf-8")

    # Warm cache
    config_cache.warm_cache("file1.json", "file2.json")

    # Verify both files are cached
    assert len(config_cache._CACHE) == 2
    assert config_cache._CACHE["file1.json"] == {"a": 1}
    assert config_cache._CACHE["file2.json"] == {"b": 2}
