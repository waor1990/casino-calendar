from datetime import datetime
from typing import Any, cast

from casino_calendar.dash_app.layout.components import modals
from casino_calendar.dash_app.layout.components.modals import _build_casino_index_entry, build_casino_index_modal


def test_build_casino_index_modal_renders_entries():
    modal = build_casino_index_modal(
        [
            {
                "name": "Example Casino",
                "color": "#ff00ff",
                "address": "123 Main St",
                "hours": "24/7",
                "distance": "Nearby",
                "note": "Test field",
            }
        ]
    )

    modal_children = cast(list[Any], modal.children)
    modal_content = cast(Any, modal_children[0])
    body_children = cast(list[Any], modal_content.children)
    body = cast(Any, body_children[1])
    entry_children = cast(list[Any], body.children)
    entry = cast(Any, entry_children[0])

    assert entry.className == "casino-index-entry"
    assert entry.style["--bg"] == "#ff00ff"
    assert entry.style["--bg-dark"] == "#ff00ff"

    fields = cast(list[Any], entry.children[1].children)
    labels = [field.children[0].children for field in fields]
    assert "Address:" in labels
    assert "Hours:" in labels
    assert "Distance:" in labels
    assert "Note:" in labels


def test_build_casino_index_entry_handles_missing_fields():
    entry = _build_casino_index_entry({"name": "No Details"})

    assert entry.children[0].children == "No Details"
    field_block = cast(Any, entry.children[1])
    assert "No additional details" in field_block.children[0].children


def test_hours_field_only_shows_current_day(monkeypatch):
    class DummyDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # pragma: no cover - deterministic override
            return datetime(2024, 6, 3)  # Monday

    monkeypatch.setattr(modals, "datetime", DummyDatetime)

    entry = _build_casino_index_entry(
        {
            "name": "Example Casino",
            "hours": {"Monday": "9am-5pm", "Tuesday": "10am-6pm"},
        }
    )

    hours_field = next(field for field in entry.children[1].children if field.children[0].children == "Hours:")
    assert hours_field.children[1].children == "9am-5pm"


def test_hours_field_parses_multiline_string(monkeypatch):
    class DummyDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # pragma: no cover - deterministic override
            return datetime(2024, 6, 4)  # Tuesday

    monkeypatch.setattr(modals, "datetime", DummyDatetime)

    entry = _build_casino_index_entry(
        {
            "name": "Example Casino",
            "address": "123 Main St",
            "hours": "Monday: 9am-5pm\nTuesday: 10am-6pm",
        }
    )

    hours_children = cast(list[Any], entry.children[1].children)
    hours_field = next(field for field in hours_children if field.children[0].children == "Hours:")
    assert hours_field.children[1].children == "10am-6pm"
