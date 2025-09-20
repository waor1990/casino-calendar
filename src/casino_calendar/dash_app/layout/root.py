"""Top-level layout factory for the Casino Calendar Dash app."""

from __future__ import annotations

from dash import Dash, dcc, html

from casino_calendar.logging.config import setup_logger

from .components.header import build_header
from .components.modals import build_day_modal, build_event_modal
from .components.stores import (
    build_hidden_helpers,
    build_intervals,
    build_state_stores,
)

logger = setup_logger(__name__)


def create_layout(app: Dash, events) -> html.Div:
    """Return the root layout for the Dash application."""

    logger.info("Creating application layout")
    logger.debug("Creating layout for %d events", len(events))

    try:
        layout = html.Div(
            className="main-layout",
            children=[
                dcc.Location(id="home-url", refresh=True),
                html.Div(
                    id="app-header",
                    children=[
                        build_header(events),
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
                            ],
                        ),
                    ],
                ),
                *build_state_stores(),
                *build_hidden_helpers(),
                *build_intervals(),
                build_event_modal(),
                build_day_modal(),
            ],
        )

        logger.info("Application layout created successfully")
        return layout

    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Error creating layout: %s", exc, exc_info=True)
        raise


__all__ = ["create_layout"]
