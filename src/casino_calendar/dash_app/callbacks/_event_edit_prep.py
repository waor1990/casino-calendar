"""Auxiliary callback to prepare event edit form and context.

This file contains a small helper callback that mirrors the grid-event/day-click
handling used by the main `show_event_modal` callback but only returns two
outputs: the form children for `event-edit-form-container` and the
`event-edit-context` store data. Splitting this out keeps the original
`show_event_modal` signature intact for existing tests while restoring the
visible edit form behavior in the UI.
"""

from __future__ import annotations

import ast
import json
from typing import Any

import dash
import pandas as pd
from dash import ALL, Input, Output, State, no_update

from casino_calendar.logging.config import setup_logger
from ..services.event_editing import build_event_modal_children, build_form_defaults

logger = setup_logger(__name__)


def register_edit_prep_callback(app, df, repository=None):
    """Register the prepare callback which fills the edit form and context.

    This callback is intentionally narrow in scope: it attempts to detect the
    same grid-event or day-event triggers that cause the modal to open and,
    when an actual event is being opened for editing, returns the form
    children and a minimal context object containing EventID, Casino, and
    Location.
    """

    @app.callback(
        Output("event-edit-form-container", "children"),
        Output("event-edit-context", "data"),
        Output("event-save-status", "children"),
        Output("event-save-status", "className"),
        Input("day-event-catcher", "clickData"),
        Input("close-modal", "n_clicks"),
        Input("close-timer", "n_intervals"),
        Input("close-day-modal", "n_clicks"),
        Input({"type": "grid-event", "index": ALL}, "n_clicks"),
        Input({"type": "grid-event", "index": ALL}, "n_clicks_timestamp"),
        Input({"type": "day-column", "index": ALL}, "n_clicks"),
        State({"type": "grid-event", "index": ALL}, "n_clicks_timestamp"),
        State({"type": "day-column", "index": ALL}, "n_clicks_timestamp"),
        State({"type": "grid-event", "index": ALL}, "id"),
        State({"type": "day-column", "index": ALL}, "id"),
        State("week-offset", "data"),
        State("screen-width", "data"),
        State("selected-casinos", "data"),
        prevent_initial_call=True,
    )
    def prepare_event_edit(
        day_click: dict | None,
        _close_clicks: int,
        _timer_tick: int,
        _close_day_clicks: int,
        _grid_clicks: list[int],
        _grid_click_timestamps_input: list[int | None],
        _day_column_clicks: list[int],
        _grid_click_timestamps_state: list[int | None] | None,
        _day_column_timestamps: list[int | None] | None,
        _grid_click_ids: list[dict[str, Any]] | None,
        _day_column_ids: list[dict[str, Any]] | None,
        week_offset: int | None = None,
        screen_width: int | None = None,
        selected_casinos: list[str] | None = None,
    ) -> tuple[Any, dict[str, Any] | None, Any, str]:
        """Detect an event open trigger and return the form and context.

        The implementation intentionally mirrors the minimal grid-event logic
        from the main callback so it will populate the edit form whenever the
        modal opens due to a grid click or a day-chart click that carries full
        event data. For other triggers it returns PreventUpdate via no_update.
        """

        ctx = dash.callback_context
        triggered_id = ctx.triggered_id
        # Normalize pattern IDs that Dash may provide as JSON strings
        if isinstance(triggered_id, str):
            try:
                triggered_id = json.loads(triggered_id)
            except Exception:
                try:
                    triggered_id = ast.literal_eval(triggered_id)
                except Exception:
                    pass

        try:
            # Prefer freshest data from repository when available
            try:
                events_df = repository.get_events() if repository is not None else df
            except Exception:
                events_df = df
            # Handle grid-event pattern clicks
            if (
                isinstance(triggered_id, dict)
                and triggered_id.get("type") == "grid-event"
            ):
                # The triggered_id contains the "index" which is the actual dataframe index
                idx = triggered_id.get("index")
                if idx is None or idx not in events_df.index:
                    # couldn't resolve event index from the grid-event click
                    # maintain consistent return types (fourth value is className str)
                    return no_update, None, no_update, ""

                row = events_df.loc[idx]
                form_defaults = build_form_defaults(row)
                _, form_component = build_event_modal_children(row, form_defaults)
                event_context = {
                    "EventID": str(row.get("EventID", "")),
                    "Casino": str(row.get("Casino", "")),
                    "Location": str(row.get("Location", "")),
                }
                # Clear any previous save status when opening the form
                return form_component, event_context, "", "event-save-status"

            # Handle day chart click that contains event payload
            if (
                triggered_id == "day-event-catcher"
                and day_click
                and "points" in day_click
                and day_click["points"]
            ):
                try:
                    data = day_click["points"][0].get("customdata", [None])[0]
                except Exception:
                    data = None
                if (
                    data
                    and isinstance(data, dict)
                    and all(
                        k in data
                        for k in [
                            "EventName",
                            "Casino",
                            "OfferType",
                            "StartDate",
                            "EndDate",
                            "Offer",
                        ]
                    )
                ):
                    series = pd.Series(data)
                    form_defaults = build_form_defaults(series)
                    _, form_component = build_event_modal_children(
                        series, form_defaults
                    )
                    event_context = {
                        "EventID": str(data.get("EventID", "")),
                        "Casino": str(data.get("Casino", "")),
                        "Location": str(data.get("Location", "")),
                    }
                    return form_component, event_context, "", "event-save-status"

            # Otherwise don't populate the edit form
            # Keep return types consistent: (children, context, status_children, status_class)
            return no_update, None, no_update, ""

        except Exception as exc:
            logger.error("prepare_event_edit callback failed: %s", exc, exc_info=True)
            return no_update, None, no_update, ""

    return prepare_event_edit
