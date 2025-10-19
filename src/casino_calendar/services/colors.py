"""Colour palette helpers used throughout the Casino Calendar UI."""

import logging
from typing import Dict

from casino_calendar.logging.config import setup_logger
from casino_calendar.services.config_cache import get_config

# Initialize module logger
logger = setup_logger(__name__)

# Cache for color data - populated lazily
_color_map = None
_default_colors = None
_generated_log_emitted = False
_fallback_color_cache: Dict[str, dict[str, str]] = {}


def _get_color_map():
    """Get casino color mapping, loading from cache if needed."""
    global _color_map
    if _color_map is None:
        _color_map = get_config("lookups/casino_colors.json") or {}
        if _color_map:
            logger.debug("Loaded casino colors for %d casinos", len(_color_map))
        else:
            logger.warning("Casino colors unavailable, falling back to defaults")
    return _color_map


def _get_default_colors():
    """Get default color list, loading from cache if needed."""
    global _default_colors
    if _default_colors is None:
        _default_colors = get_config("lookups/default_colors.json") or []
        if _default_colors:
            logger.debug("Loaded %d default colors", len(_default_colors))
        else:
            logger.warning("Default colors unavailable")
    return _default_colors


def get_color():
    """Return a mapping of casino names to color styles."""
    global _generated_log_emitted

    color_map = _get_color_map()
    default_colors = _get_default_colors()

    result = {}
    for casino, colors in color_map.items():
        result[casino] = colors

    if not result:
        logger.warning("No casino colors found, using default colors")
        dummy_casinos = [f"Casino {i}" for i in range(len(default_colors))]
        for casino_name, color in zip(dummy_casinos, default_colors, strict=False):
            result[casino_name] = {"bg": color, "text": "#000000"}

    if logger.isEnabledFor(logging.DEBUG) and not _generated_log_emitted:
        logger.debug("Generated colors for %d casinos", len(result))
        _generated_log_emitted = True
    return result


def _is_perceived_light(color: str) -> bool:
    """Return True when ``color`` is considered light for contrast decisions."""

    hex_value = color.lstrip("#")
    if len(hex_value) == 3:
        hex_value = "".join(c * 2 for c in hex_value)

    try:
        red = int(hex_value[0:2], 16)
        green = int(hex_value[2:4], 16)
        blue = int(hex_value[4:6], 16)
    except (ValueError, IndexError):
        return True

    brightness = 0.299 * red + 0.587 * green + 0.114 * blue
    return brightness >= 150


def resolve_casino_color(
    casino_name: str,
    palette: dict[str, dict[str, str]] | None = None,
) -> dict[str, str]:
    """Return a color style for ``casino_name`` with resilient fallbacks."""

    color_palette = palette or get_color()
    if casino_name in color_palette:
        return color_palette[casino_name]

    if casino_name in _fallback_color_cache:
        return _fallback_color_cache[casino_name]

    default_colors = _get_default_colors()
    if default_colors:
        index = abs(hash(casino_name)) % len(default_colors)
        bg_color = default_colors[index]
    else:
        bg_color = "#627D98"

    text_color = "#000000" if _is_perceived_light(bg_color) else "#ffffff"
    style = {"bg": bg_color, "text": text_color}
    _fallback_color_cache[casino_name] = style
    logger.debug("Assigned fallback color for %s -> %s", casino_name, style)
    return style
