"""Top-level layout factory for the Casino Calendar Dash application."""

from __future__ import annotations

from dash import Dash, dcc, html

from casino_calendar.logging import config as logging_config

from .components import header as header_components
from .components import modals as modal_components
from .components import stores as store_components

logger = logging_config.setup_logger(__name__)


def create_layout(app: Dash, events) -> html.Div:
    """Return the root layout for the Dash application."""

    logger.info("Building application layout")
    logger.debug("Preparing layout for %d events", len(events))

    try:
        layout = html.Div(
            className="main-layout",
            children=[
                dcc.Location(id="home-url", refresh=True),
                html.Div(
                    id="app-header",
                    children=[
                        header_components.build_header(events),
                        html.Div(
                            id="calendar-scroll-body",
                            className="calendar-scroll-body",
                            children=[
                                dcc.Loading(
                                    id="calendar-loading",
                                    type="circle",
                                    color="#6A5ACD",
                                    children=html.Div(
                                        id="week-chart-container",
                                        className="week-gap section-margin calendar-content",
                                    ),
                                ),
                                html.Div(id="calendar-grid", style={"display": "none"}),
                            ],
                        ),
                    ],
                ),
                *store_components.build_state_stores(),
                *store_components.build_hidden_helpers(),
                *store_components.build_intervals(),
                modal_components.build_event_modal(),
                modal_components.build_day_modal(),
            ],
        )

        logger.info("Application layout ready")
        return layout

    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to build layout: %s", exc, exc_info=True)
        raise


__all__ = ["create_layout"]
