import time
from dash import Dash

# Load environment variables from .env file early
try:
    from dotenv import load_dotenv

    load_dotenv()  # Load .env file before importing other modules
except ImportError:
    pass

from app_components.callbacks import register_callbacks
from app_components.data import load_event_data
from app_components.layout import create_layout
from app_components.logging_config import setup_logger

# Initialize application logger
logger = setup_logger(__name__)

app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "Casino Event Calendar"

logger.info("Casino Calendar application starting up")
logger.debug(f"Dash app initialized with title: {app.title}")

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
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

logger.info("Loading event data...")
start_time = time.time()
df_events = load_event_data()
load_time = time.time() - start_time
logger.info(f"Event data loaded successfully in {load_time:.3f}s")
logger.debug(f"Loaded {len(df_events)} events from data source")

logger.info("Creating application layout...")
app.layout = create_layout(app, df_events)
logger.debug("Application layout created successfully")

logger.info("Registering callbacks...")
register_callbacks(app, df_events)
logger.debug("Callbacks registered successfully")

server = app.server

# Run the Dash app
if __name__ == "__main__":
    # Check environment for debug mode (defaults to False)
    import os

    debug_mode = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes", "on")

    if debug_mode:
        logger.info("Starting Casino Calendar application in development mode")
        logger.warning("Debug mode is enabled - not suitable for production")
    else:
        logger.info("Starting Casino Calendar application in production mode")

    try:
        app.run(debug=debug_mode)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.critical(f"Application failed to start: {e}")
        raise
    finally:
        logger.info("Application shutdown complete")
