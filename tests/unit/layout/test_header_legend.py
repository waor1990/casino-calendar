"""Unit tests for the casino legend UI components."""

from __future__ import annotations

import pandas as pd

from casino_calendar.dash_app.layout.components import header
from casino_calendar.services import colors


def test_create_legend_adds_fallback_color_and_hint(monkeypatch):
    fallback_color = "#ABCDEF"
    monkeypatch.setattr(colors, "_fallback_color_cache", {})
    df = pd.DataFrame({"Casino": ["Mapped Casino", "Unseen Casino", "Unseen Casino"]})

    monkeypatch.setattr(
        header,
        "get_color",
        lambda: {"Mapped Casino": {"bg": "#111111", "text": "#ffffff"}},
    )
    monkeypatch.setattr(colors, "_get_default_colors", lambda: [fallback_color])

    legend_items = header.create_legend(df)

    assert len(legend_items) == 2

    unseen_entry = next(item for item in legend_items if item.id["index"] == "Unseen Casino")
    color_box = unseen_entry.children[0]
    labels = unseen_entry.children[1].children

    assert color_box.style["backgroundColor"].lower() == fallback_color.lower()

    legend_text = labels[0].to_plotly_json()
    assert legend_text["props"]["data-color"].lower() == fallback_color.lower()

    hint = next(child for child in labels[1:] if getattr(child, "className", None) == "legend-hint")
    assert "lookups/casino_colors.json" in hint.children
