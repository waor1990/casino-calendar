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
        # Cycle through: light -> dark1 -> dark2 -> dark3 -> dark4 -> dark5 -> light
        theme_cycle = ["light", "dark1", "dark2", "dark3", "dark4", "dark5"]

        try:
            current_index = theme_cycle.index(current)
            next_index = (current_index + 1) % len(theme_cycle)
        except (ValueError, TypeError):
            next_index = 1  # Default to dark1 if current theme is invalid

        new_theme = theme_cycle[next_index]
        logger.info(f"Theme cycled from '{current}' to '{new_theme}'")
        return new_theme

    app.clientside_callback(
        """
        function(theme) {
            var root = document.documentElement;
            var btn = document.getElementById('theme-toggle');
            
            // Background color options for testing
            var backgrounds = {
                'light': null,  // Use default light theme
                'dark1': '#1e1b22',  // Deep purple-gray (current)
                'dark2': '#1a1a1c',  // Warm charcoal
                'dark3': '#212121',  // Material Design dark
                'dark4': '#1f2937',  // Tailwind gray-800
                'dark5': '#252230'   // Lighter purple-gray
            };
            
            var emojis = {
                'light': '🌙',
                'dark1': '🌑',
                'dark2': '🌒', 
                'dark3': '🌓',
                'dark4': '🌔',
                'dark5': '☀️'
            };
            
            // Remove all theme attributes first
            root.removeAttribute('data-theme');
            root.style.removeProperty('--color-background-override');
            
            if (theme && theme.startsWith('dark')) {
                root.setAttribute('data-theme', 'dark');
                var bgColor = backgrounds[theme];
                if (bgColor) {
                    root.style.setProperty('--color-background-override', bgColor);
                    // Override the CSS variable
                    root.style.setProperty('--color-background', bgColor);
                }
            }
            
            if (btn) {
                btn.textContent = emojis[theme] || '🌙';
                btn.title = theme === 'light' ? 'Switch to dark theme' : 
                           'Current: ' + theme + ' - Click to cycle backgrounds';
            }
            
            return '';
        }
        """,
        Output("theme-dummy", "children"),
        Input("theme-store", "data"),
    )
    logger.debug("Registered clientside callback for theme application")

    logger.info("Theme callbacks registered successfully")
