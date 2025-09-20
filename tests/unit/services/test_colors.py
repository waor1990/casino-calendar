"""Unit tests for color service helpers."""

from __future__ import annotations

from casino_calendar.services import colors


def _reset_color_caches():
    colors._color_map = None  # type: ignore[attr-defined]
    colors._default_colors = None  # type: ignore[attr-defined]
    colors._generated_log_emitted = False  # type: ignore[attr-defined]


def test_get_color_returns_configured_values(monkeypatch):
    _reset_color_caches()

    def fake_get_config(path: str):
        if "casino_colors" in path:
            return {"Test Casino": {"bg": "#fff", "text": "#000"}}
        if "default_colors" in path:
            return ["#123456"]
        raise AssertionError(f"Unexpected path {path}")

    monkeypatch.setattr(colors, "get_config", fake_get_config)

    result = colors.get_color()
    assert result == {"Test Casino": {"bg": "#fff", "text": "#000"}}


def test_get_color_falls_back_to_defaults(monkeypatch):
    _reset_color_caches()

    def fake_get_config(path: str):
        if "default_colors" in path:
            return ["#123456", "#abcdef"]
        return {}

    monkeypatch.setattr(colors, "get_config", fake_get_config)

    result = colors.get_color()
    assert len(result) == 2
    assert all("bg" in entry and "text" in entry for entry in result.values())
