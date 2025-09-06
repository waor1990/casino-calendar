from dash import Input, Output

from ..logging_config import setup_logger

logger = setup_logger(__name__)


def register_callbacks(app, _df) -> None:
    """Register navigation callbacks."""
    logger.info("Registering navigation callbacks")

    @app.callback(
        Output("home-url", "pathname"),
        Input("home-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def _navigate_home(_n_clicks: int) -> str:  # pragma: no cover - simple redirect
        """Return root path when home button is clicked."""
        logger.debug(f"Home button clicked: {_n_clicks}")
        return "/"

    logger.info("Navigation callbacks registered successfully")
