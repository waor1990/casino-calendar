"""Utilities for loading and enriching casino index metadata.

The casino index powers the dedicated modal that lists participating
casinos alongside helpful details (address, hours, distance, etc.). Data
is sourced from ``data/lookups/casino_index.json`` and supplemented with
existing colour lookups so the UI can render consistent accents even when
explicit colours are omitted from the index file.
"""

from __future__ import annotations

from typing import Any

from casino_calendar.logging.config import setup_logger
from casino_calendar.services.colors import resolve_casino_color
from casino_calendar.services.config_cache import get_config

logger = setup_logger(__name__)

CASINO_INDEX_LOOKUP = "lookups/casino_index.json"


def load_casino_index() -> list[dict[str, Any]]:
    """Return the ordered list of casino metadata entries.

    Each entry must include a ``name`` field and may provide ``color``,
    ``address``, ``hours``, and ``distance`` properties. Additional keys
    are preserved and rendered by the modal to keep the lookup file
    extensible. When a colour is not defined, the value falls back to the
    standard casino colour palette so styling remains consistent.
    """

    data = get_config(CASINO_INDEX_LOOKUP) or []
    if not isinstance(data, list):
        logger.error("Casino index data must be a list; received %s", type(data))
        return []

    entries: list[dict[str, Any]] = []
    for raw_entry in data:
        if not isinstance(raw_entry, dict):
            logger.warning("Skipping non-dict casino index entry: %s", raw_entry)
            continue

        entry = dict(raw_entry)
        casino_name = entry.get("name")

        if casino_name and not entry.get("color"):
            resolved_colors = resolve_casino_color(casino_name)
            entry["color"] = resolved_colors.get("bg")

        entries.append(entry)

    logger.debug("Loaded %d casino index entries", len(entries))
    return entries


__all__ = ["load_casino_index"]
