"""Callbacks responsible for handling the light/dark theme toggle."""

from casino_calendar.logging.config import setup_logger
from dash import Input, Output, State

# Initialize module logger
logger = setup_logger(__name__)


def register_callbacks(app, _df) -> None:
    """Register theme toggle callbacks."""
    logger.info("Registering theme callbacks")

    @app.callback(
        Output("theme-store", "data"),
        Input("theme-toggle", "n_clicks"),
        State("theme-store", "data"),
        prevent_initial_call=True,
    )
    def toggle_theme(_n_clicks: int, current: str) -> str:
        # Simple light/dark toggle with dark3 as the dark theme
        logger.debug(
            "Theme toggle clicked %s time(s); current theme %s", _n_clicks, current
        )

        if current == "light":
            new_theme = "dark"
        else:
            new_theme = "light"

        logger.info("Theme changed from %s to %s", current, new_theme)
        return new_theme

    app.clientside_callback(
        """
        function(theme) {
            console.log('[CasinoCalendar] Theme toggle received', theme);
            var root = document.documentElement;
            var btn = document.getElementById('theme-toggle');

            // Remove any theme attributes first
            root.removeAttribute('data-theme');
            root.style.removeProperty('--color-background-override');

            if (theme === 'dark') {
                console.log('[CasinoCalendar] Applying dark theme');
                root.setAttribute('data-theme', 'dark');
                // Set dark3 background color (#212121) as the standard dark theme
                root.style.setProperty('--color-background', '#212121');
            } else {
                console.log('[CasinoCalendar] Applying light theme');
                // Remove any custom background override for light theme
                root.style.removeProperty('--color-background');
            }

            if (btn) {
                btn.textContent = theme === 'dark' ? '☀️' : '🌙';
                btn.title = theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme';
                console.log('[CasinoCalendar] Updated button for theme', theme);
            }

            if (window.CasinoCalendar && typeof window.CasinoCalendar.updateLegendTextColors === 'function') {
                try {
                    window.CasinoCalendar.updateLegendTextColors(theme === 'dark' ? 'dark' : 'light');
                } catch (error) {
                    console.error('[CasinoCalendar] Failed to update legend text colors', error);
                }
            }

            return '';
        }
        """,
        Output("theme-dummy", "children"),
        Input("theme-store", "data"),
    )
    logger.debug("Clientside theme callback registered")

    logger.info("Theme callbacks ready")
