"""Callbacks for the Casino Index modal."""

from __future__ import annotations

from typing import Any, Tuple

import dash
from dash import Input, Output

from casino_calendar.logging.config import setup_logger

logger = setup_logger(__name__)


def register_callbacks(app, _df) -> None:
    """Register callbacks that open and close the casino index modal."""

    logger.info("Registering casino index callbacks")

    @app.callback(
        Output("casino-index-modal", "className"),
        Output("casino-index-modal", "style"),
        Input("open-casino-index-modal", "n_clicks"),
        Input("close-casino-index-modal", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_casino_index_modal(open_clicks: int, close_clicks: int) -> Tuple[str, dict[str, Any]]:
        """Open the casino index modal on click and close when requested."""

        ctx = dash.callback_context
        triggered_id = getattr(ctx, "triggered_id", None)
        logger.debug("Casino index modal trigger: %s", triggered_id)

        base_class = "modal"

        if triggered_id == "close-casino-index-modal":
            return base_class, {"display": "none"}

        return f"{base_class} show", {}

    logger.info("Casino index callbacks ready")


__all__ = ["register_callbacks"]
