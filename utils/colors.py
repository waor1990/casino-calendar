from app_components.logging_config import setup_logger
from utils.config_cache import get_config

# Initialize module logger
logger = setup_logger(__name__)

COLOR_MAP = get_config("casino_colors.json") or {}
if COLOR_MAP:
    logger.debug("Loaded casino colors for %d casinos", len(COLOR_MAP))
else:
    logger.warning("Casino colors unavailable, falling back to defaults")

DEFAULT_COLORS = get_config("default_colors.json") or []
if DEFAULT_COLORS:
    logger.debug("Loaded %d default colors", len(DEFAULT_COLORS))
else:
    logger.warning("Default colors unavailable")


def get_color():
    """Return a mapping of casino names to color styles."""
    logger.debug("Generating color mapping for casinos")

    color_map = COLOR_MAP
    default_colors = DEFAULT_COLORS

    result = {}
    for casino, colors in color_map.items():
        result[casino] = colors

    if not result:
        logger.warning("No casino colors found, using default colors")
        dummy_casinos = [f"Casino {i}" for i in range(len(default_colors))]
        for casino_name, color in zip(dummy_casinos, default_colors):
            result[casino_name] = {"bg": color, "text": "#000000"}

    logger.debug(f"Generated colors for {len(result)} casinos")
    return result
