"""Header and legend components for the Casino Calendar UI."""

from __future__ import annotations

from typing import Any

import pandas as pd
from casino_calendar.logging.config import setup_logger
from casino_calendar.services.colors import get_color
from dash import dcc, html

logger = setup_logger(__name__)

LEGEND_CASINOS: list[str] = []


def build_header(events: pd.DataFrame) -> html.Div:
    """Return the sticky page header composed of controls and legend."""

    logger.debug("Building sticky header")

    return html.Div(
        [
            html.H1(
                [
                    html.Button(
                        "🎰 Casino Event Calendar 📅",
                        id="home-button",
                        n_clicks=0,
                        className="calendar-title-home-button",
                        title="Home",
                    ),
                    html.Button(
                        "🌙",
                        id="theme-toggle",
                        n_clicks=0,
                        className="emoji-button theme-toggle",
                        title="Toggle dark mode",
                    ),
                ],
                className="calendar-title",
            ),
            html.Div(
                id="header-container",
                className="legend-container",
                children=[
                    html.Button(
                        "🎲",
                        id="prev-button",
                        title="Prior Week",
                        n_clicks=0,
                        className="emoji-button",
                    ),
                    html.Div(
                        [
                            html.Legend(
                                "Casino Legend:",
                                className="legend-title legend-gap",
                            ),
                            html.Div(create_legend(events), className="legend-container"),
                            dcc.Dropdown(
                                id="event-type-filter",
                                options=[
                                    {"label": offer_type, "value": offer_type}
                                    for offer_type in sorted(events["OfferType"].dropna().unique())
                                ],
                                multi=True,
                                placeholder="Filter by event type",
                                className="event-type-dropdown",
                                value=[],
                            ),
                            html.Div(
                                id="hotel-booking-container",
                                style={
                                    "display": "none",
                                    "textAlign": "center",
                                    "marginTop": "10px",
                                },
                                children=[],
                            ),
                        ],
                        style={"flex": "1"},
                    ),
                    html.Div(
                        [
                            html.Button(
                                "🎰",
                                id="next-button",
                                n_clicks=0,
                                className="emoji-button",
                            ),
                        ],
                        style={"display": "flex", "gap": "0.5rem"},
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "paddingBottom": "10px",
                    "--slide-distance": "8rem",
                },
            ),
            html.Div(id="week-label", className="fade-text week-label", children=""),
            html.Div(id="day-label-row", className="day-label-wrapper"),
        ],
        className="sticky-header",
    )


def create_legend(df: pd.DataFrame) -> list[Any]:
    """Return the casino legend buttons."""

    logger.debug("Building casino legend")
    legend_items: list[Any] = []
    LEGEND_CASINOS.clear()

    try:
        colors = get_color()
        unique_casinos = df["Casino"].unique()
        logger.debug("Unique casinos found: %d", len(unique_casinos))

        for casino, color in colors.items():
            if casino in unique_casinos:
                LEGEND_CASINOS.append(casino)
                legend_items.append(
                    html.Button(
                        className="legend-item legend-button",
                        id={"type": "casino-filter", "index": casino},
                        n_clicks=0,
                        children=[
                            html.Div(
                                className="legend-color-box",
                                style={"backgroundColor": color["bg"]},
                            ),
                            html.Span(
                                f"{casino}",
                                className="legend-text legend-gap",
                                style={"color": color["bg"], "marginRight": "4px"},
                            ),
                        ],
                    )
                )

        logger.info("Generated %d legend entries", len(legend_items))
        return legend_items

    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to build legend: %s", exc, exc_info=True)
        return []


__all__ = ["LEGEND_CASINOS", "build_header", "create_legend"]
