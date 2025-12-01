"""Header and legend components for the Dash layout."""

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

    offer_series = events["OfferType"].dropna().astype(str)
    offer_counts = offer_series.value_counts()
    offer_types = sorted(offer_counts.index.tolist())
    dropdown_options = [
        {
            "label": f"{offer_type} ({offer_counts.get(offer_type, 0)})",
            "value": offer_type,
        }
        for offer_type in offer_types
    ]
    longest_label = max(
        (len(option["label"]) for option in dropdown_options),
        default=len("Filter by event type"),
    )
    dropdown_min_width = longest_label + 2

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        className="header-title-spacer", **{"aria-hidden": "true"}
                    ),
                    html.H1(
                        html.Button(
                            "🎰 Casino Event Calendar 📅",
                            id="home-button",
                            n_clicks=0,
                            className="calendar-title-home-button",
                            title="Home",
                        ),
                        className="calendar-title",
                    ),
                    html.Div(
                        className="header-title-spacer", **{"aria-hidden": "true"}
                    ),
                ],
                className="header-title-row",
            ),
            html.Div(
                html.Button(
                    "🌙",
                    id="theme-toggle",
                    n_clicks=0,
                    className="emoji-button theme-toggle",
                    title="Toggle dark mode",
                ),
                className="theme-toggle-fab",
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
                            html.Span(
                                "Casino Legend:",
                                className="legend-title legend-gap",
                            ),
                            html.Div(
                                create_legend(events), className="legend-container"
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
            html.Div(
                dcc.Dropdown(
                    id="event-type-filter",
                    options=dropdown_options,
                    multi=True,
                    placeholder="Filter by event type",
                    className="event-type-dropdown",
                    value=[],
                    searchable=False,
                    style={
                        "width": "auto",
                        "minWidth": f"{dropdown_min_width}ch",
                        "maxWidth": "100%",
                    },
                ),
                className="event-filter-row",
            ),
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
                base_color = color["bg"]
                dark_theme_color = color.get("bg_dark") or base_color
                legend_text_style: dict[str, str] = {
                    "color": base_color,
                    "marginRight": "4px",
                }
                legend_data_attributes = {
                    "data-color": base_color,
                    "data-dark-color": dark_theme_color,
                }

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
                                style=legend_text_style,
                                **legend_data_attributes,
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
