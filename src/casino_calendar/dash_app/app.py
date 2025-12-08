"""Dash application factory and runtime helpers for Casino Calendar."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Tuple

import requests  # type: ignore
from dash import Dash

from casino_calendar.logging.config import setup_logger
from casino_calendar.services.config_cache import warm_cache
from casino_calendar.settings import get_env, get_env_bool

from .callbacks import register_callbacks
from .data import APIEventRepository
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


def _wait_for_api(
    api_url: str, max_retries: int = 10, retry_delay: float = 0.5
) -> bool:
    """Check if the API is available and ready to serve requests.

    Args:
        api_url: The base URL of the API (e.g., http://localhost:5001)
        max_retries: Maximum number of connection attempts
        retry_delay: Delay in seconds between retries

    Returns:
        True if API is available, False if max retries exceeded
    """
    health_url = f"{api_url}/events"

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(health_url, timeout=2)
            if response.status_code == 200:
                logger.info("API is healthy and responding")
                return True
        except (requests.ConnectionError, requests.Timeout) as e:
            logger.debug(
                "API connection attempt %d/%d failed: %s", attempt, max_retries, e
            )
            if attempt < max_retries:
                time.sleep(retry_delay)

    logger.error(
        "Failed to connect to API at %s after %d attempts. "
        "Please ensure the API is running (e.g., python api/event_api.py)",
        api_url,
        max_retries,
    )
    return False


def create_dash_app() -> Tuple[Dash, Any]:
    """Create and configure the Dash application."""

    logger.info("Starting Casino Calendar application")

    project_root = Path(__file__).resolve().parents[3]
    assets_path = project_root / "assets"
    logger.debug("Assets folder: %s", assets_path)

    app = Dash(
        __name__,
        suppress_callback_exceptions=True,
        assets_folder=str(assets_path),
        assets_ignore=r".*\.scss$",
    )
    app.title = "Casino Events Calendar"
    app.index_string = _build_index_string()
    logger.debug("Dash app title set to %s", app.title)

    # Preload configuration files so they are cached at startup
    warm_cache(
        "lookups/casino_colors.json",
        "lookups/default_colors.json",
        "lookups/offer_type_emojis.json",
        "lookups/offer_keywords.json",
        "lookups/hotel_book_sites.json",
    )

    api_base_url = get_env("EVENT_API_BASE_URL", "http://localhost:5001")
    if not api_base_url:
        api_base_url = "http://localhost:5001"

    # Optionally check if API is available before proceeding. This can be
    # disabled in test environments by setting WAIT_FOR_API=false.
    # Default to not waiting in test environments; enable via env var when
    # running the full stack locally or in production.
    wait_for_api = get_env_bool("WAIT_FOR_API", False)
    logger.info("Checking API availability at %s (wait=%s)", api_base_url, wait_for_api)
    if wait_for_api:
        if not _wait_for_api(api_base_url):
            logger.error(
                "Cannot proceed without API. Please start the API and try again."
            )
            raise RuntimeError(
                f"Event API at {api_base_url} is not available. "
                "Please start it with: python api/event_api.py"
            )
    else:
        logger.debug("Skipping API availability check due to WAIT_FOR_API=false")

    repository = APIEventRepository(base_url=api_base_url)

    logger.info("Loading event data")
    start_time = time.time()
    events = repository.get_events()
    load_time = time.time() - start_time
    logger.info("Loaded event data in %.3f seconds", load_time)
    logger.debug("Event count: %d", len(events))

    logger.info("Building application layout")

    def _serve_layout():
        return create_layout(app, events)

    app.layout = _serve_layout
    logger.debug("Application layout ready")

    logger.info("Registering callbacks")
    register_callbacks(app, events, repository)
    logger.debug("Callbacks ready")

    return app, app.server


def run_app(app: Dash | None = None) -> None:
    """Run the Dash development server respecting the DEBUG flag."""

    if app is None:
        app, _ = create_dash_app()

    debug_mode = get_env_bool("DEBUG", False)

    if debug_mode:
        logger.info("Starting development server")
        logger.warning("Debug mode is enabled; avoid using in production")
    else:
        logger.info("Starting production server")

    try:
        app.run(debug=debug_mode)
    except KeyboardInterrupt:  # pragma: no cover - manual shutdown
        logger.info("Server stopped by user")
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.critical("Server failed to start: %s", exc)
        raise
    finally:
        logger.info("Server shutdown complete")


__all__ = ["create_dash_app", "run_app"]
