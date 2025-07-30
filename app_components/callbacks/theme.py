from dash import Input, Output, State

from ..logging_config import setup_logger

# Initialize module logger
logger = setup_logger(__name__)


def register_callbacks(app, _df) -> None:
    """Register theme toggle callbacks."""
    logger.info("Registering theme toggle callbacks")

    @app.callback(
        Output("theme-store", "data"),
        Input("theme-toggle", "n_clicks"),
        State("theme-store", "data"),
        prevent_initial_call=True,
    )
    def toggle_theme(_n_clicks: int, current: str) -> str:
        new_theme = "light" if current == "dark" else "dark"
        logger.info(f"Theme toggled from '{current}' to '{new_theme}'")
        return new_theme

    app.clientside_callback(
        """
        function(theme) {
            var root = document.documentElement;
            var btn = document.getElementById('theme-toggle');
            var dark = theme === 'dark';
            if (dark) {
                root.setAttribute('data-theme', 'dark');
            } else {
                root.removeAttribute('data-theme');
            }
            if (btn) {
                btn.textContent = dark ? '☀️' : '🌙';
            }
            return '';
        }
        """,
        Output("theme-dummy", "children"),
        Input("theme-store", "data"),
    )
    logger.debug("Registered clientside callback for theme application")

    logger.info("Theme callbacks registered successfully")
