"""Dash application factory for Casino Calendar."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Tuple

from casino_calendar.logging.config import setup_logger
from casino_calendar.services.config_cache import warm_cache
from casino_calendar.settings import get_env_bool
from dash import Dash

from .callbacks import register_callbacks
from .data import EventRepository
from .layout.root import create_layout

logger = setup_logger(__name__)


def _build_index_string() -> str:
    """Return a custom HTML index string for Dash."""

    return """
<!DOCTYPE html>
<html>
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


def create_dash_app() -> Tuple[Dash, Any]:
    """Create and configure the Dash application."""

    logger.info("Casino Calendar application starting up")

    project_root = Path(__file__).resolve().parents[3]
    assets_path = project_root / "assets"
    logger.debug("Assets folder configured at %s", assets_path)

    app = Dash(
        __name__,
        suppress_callback_exceptions=True,
        assets_folder=str(assets_path),
        assets_ignore=r".*\.scss$",
    )
    app.title = "Casino Events Calendar"
    app.index_string = _build_index_string()
    logger.debug("Dash app initialized with title: %s", app.title)

    # Preload configuration files so they are cached at startup
    warm_cache(
        "lookups/casino_colors.json",
        "lookups/default_colors.json",
        "lookups/offer_type_emojis.json",
        "lookups/offer_keywords.json",
        "lookups/hotel_book_sites.json",
    )

    repository = EventRepository()

    logger.info("Loading event data...")
    start_time = time.time()
    events = repository.load_events()
    load_time = time.time() - start_time
    logger.info("Event data loaded successfully in %.3fs", load_time)
    logger.debug("Loaded %d events from data source", len(events))

    logger.info("Creating application layout...")
    app.layout = create_layout(app, events)
    logger.debug("Application layout created successfully")

    logger.info("Registering callbacks...")
    register_callbacks(app, events)
    logger.debug("Callbacks registered successfully")

    return app, app.server


def run_app(app: Dash | None = None) -> None:
    """Run the Dash development server respecting the DEBUG flag."""

    if app is None:
        app, _ = create_dash_app()

    debug_mode = get_env_bool("DEBUG", False)

    if debug_mode:
        logger.info("Starting Casino Calendar application in development mode")
        logger.warning("Debug mode is enabled - not suitable for production")
    else:
        logger.info("Starting Casino Calendar application in production mode")

    try:
        app.run(debug=debug_mode)
    except KeyboardInterrupt:  # pragma: no cover - manual shutdown
        logger.info("Application stopped by user")
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.critical("Application failed to start: %s", exc)
        raise
    finally:
        logger.info("Application shutdown complete")


__all__ = ["create_dash_app", "run_app"]
