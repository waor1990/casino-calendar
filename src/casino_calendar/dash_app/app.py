"""Dash application factory and runtime helpers for Casino Calendar."""

from __future__ import annotations

import logging
import socket
import time
from pathlib import Path
from typing import Any, Tuple

from dash import Dash

from casino_calendar.logging.config import setup_logger
from casino_calendar.services.config_cache import warm_cache
from casino_calendar.settings import get_env, get_env_bool

from .callbacks import register_callbacks
from .data import EventRepository
from .layout.root import create_layout

logger = setup_logger(__name__)


class _DashStartupHostFilter(logging.Filter):
    def __init__(self, display_host: str, public_host: str | None, public_port: int) -> None:
        super().__init__()
        self._display_host = display_host
        self._public_host = public_host
        self._public_port = public_port

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        if isinstance(record.msg, str) and record.msg.startswith("Dash is running on") and record.args:
            args = list(record.args)
            if len(args) >= 2:
                args[1] = self._display_host
                record.args = tuple(args)
            if self._public_host:
                message = record.msg
                if not message.endswith("\n"):
                    message = f"{message}\n"
                record.msg = f"{message}Network access: http://{self._public_host}:{self._public_port}\n"
        return True


def _install_dash_startup_filter(app: Dash, display_host: str, public_host: str | None, port: int) -> None:
    dash_logger = getattr(app, "logger", None)
    if dash_logger is None:
        return

    for existing in dash_logger.filters:
        if isinstance(existing, _DashStartupHostFilter):
            existing._display_host = display_host
            existing._public_host = public_host
            existing._public_port = port
            return

    dash_logger.addFilter(_DashStartupHostFilter(display_host, public_host, port))


def _resolve_public_host(host: str) -> str | None:
    override = get_env("DASH_PUBLIC_HOST")
    if override:
        return override

    if host != "0.0.0.0":
        return None

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            address = sock.getsockname()[0]
    except OSError:
        return None

    if not address or address.startswith("127."):
        return None

    return address


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

    repository = EventRepository()

    logger.info("Loading event data")
    start_time = time.time()
    events = repository.load_events()
    load_time = time.time() - start_time
    logger.info("Loaded event data in %.3f seconds", load_time)
    logger.debug("Event count: %d", len(events))

    logger.info("Building application layout")

    def _serve_layout():
        return create_layout(app, events)

    app.layout = _serve_layout
    logger.debug("Application layout ready")

    logger.info("Registering callbacks")
    register_callbacks(app, events)
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

    host = get_env("DASH_HOST", "0.0.0.0") or "0.0.0.0"
    display_host = "localhost" if host == "0.0.0.0" else host
    public_host = _resolve_public_host(host)
    if public_host == display_host:
        public_host = None
    _install_dash_startup_filter(app, display_host, public_host, 8050)

    try:
        app.run(host=host, port=8050, debug=debug_mode)
    except KeyboardInterrupt:  # pragma: no cover - manual shutdown
        logger.info("Server stopped by user")
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.critical("Server failed to start: %s", exc)
        raise
    finally:
        logger.info("Server shutdown complete")


__all__ = ["create_dash_app", "run_app"]
