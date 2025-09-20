from uuid import uuid4

from dash import Input, Output

from casino_calendar.logging.config import setup_logger

logger = setup_logger(__name__)


def register_callbacks(app, _df) -> None:
    """Register navigation callbacks."""
    logger.info("Registering navigation callbacks")

    @app.callback(
        Output("home-url", "pathname"),
        Output("home-url", "search"),
        Input("home-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def _navigate_home(
        _n_clicks: int,
    ) -> tuple[str, str]:  # pragma: no cover - simple redirect
        """Force a navigation to home and trigger a reload.

        Adding a unique query string ensures the app fully reloads, so
        in-memory stores reset to defaults (week offset, filters, etc.).
        """
        logger.debug(f"Home button clicked: {_n_clicks}")
        return "/", f"?r={uuid4()}"

    logger.info("Navigation callbacks registered successfully")
