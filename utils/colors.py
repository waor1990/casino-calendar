import json
from pathlib import Path

from app_components.logging_config import setup_logger

# Initialize module logger
logger = setup_logger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

try:
    with open(DATA_DIR / "casino_colors.json", encoding="utf-8") as f:
        COLOR_MAP = json.load(f)
    logger.debug(f"Loaded casino colors for {len(COLOR_MAP)} casinos")
except FileNotFoundError:
    logger.error(f"Casino colors file not found: {DATA_DIR / 'casino_colors.json'}")
    COLOR_MAP = {}
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in casino colors file: {e}")
    COLOR_MAP = {}

try:
    with open(DATA_DIR / "default_colors.json", encoding="utf-8") as f:
        DEFAULT_COLORS = json.load(f)
    logger.debug(f"Loaded {len(DEFAULT_COLORS)} default colors")
except FileNotFoundError:
    logger.error(f"Default colors file not found: {DATA_DIR / 'default_colors.json'}")
    DEFAULT_COLORS = []
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in default colors file: {e}")
    DEFAULT_COLORS = []


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
