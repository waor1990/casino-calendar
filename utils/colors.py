import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
with open(DATA_DIR / "casino_colors.json", encoding="utf-8") as f:
    COLOR_MAP = json.load(f)
with open(DATA_DIR / "default_colors.json", encoding="utf-8") as f:
    DEFAULT_COLORS = json.load(f)


def get_color():
    """Return a mapping of casino names to color styles."""
    color_map = COLOR_MAP
    default_colors = DEFAULT_COLORS

    result = {}
    for casino, colors in color_map.items():
        result[casino] = colors

    if not result:
        dummy_casinos = [f"Casino {i}" for i in range(len(default_colors))]
        for casino_name, color in zip(dummy_casinos, default_colors):
            result[casino_name] = {"bg": color, "text": "#000000"}

    return result
