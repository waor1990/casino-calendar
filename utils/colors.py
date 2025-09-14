import logging

from app_components.logging_config import setup_logger
from utils.config_cache import get_config

# Initialize module logger
logger = setup_logger(__name__)

# Cache for color data - populated lazily
_color_map = None
_default_colors = None
_generated_log_emitted = False


def _get_color_map():
    """Get casino color mapping, loading from cache if needed."""
    global _color_map
    if _color_map is None:
        _color_map = get_config("casino_colors.json") or {}
        if _color_map:
            logger.debug("Loaded casino colors for %d casinos", len(_color_map))
        else:
            logger.warning("Casino colors unavailable, falling back to defaults")
    return _color_map


def _get_default_colors():
    """Get default color list, loading from cache if needed."""
    global _default_colors
    if _default_colors is None:
        _default_colors = get_config("default_colors.json") or []
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
