"""Event-related Dash callbacks for modals, overflow panels, and charts."""

import ast
import json
import time
from datetime import datetime, timedelta
from typing import Any, Tuple
from uuid import uuid4

import dash
import pandas as pd
from dash import ALL, Input, Output, State, dcc, html, no_update
from dash._callback import NoUpdate

from casino_calendar.logging.config import setup_logger
from casino_calendar.services.colors import get_color, resolve_casino_color
from casino_calendar.settings import APP_TIMEZONE

from ..services import event_editing
from ..services.layout_state import to_naive_utc
from ..visualization import charts as day_charts

PDT = APP_TIMEZONE

# Initialize module logger
logger = setup_logger(__name__)


class _NullEventRepository:
    """Fallback repository used when persistence is not configured."""

    def save_events(self, _df: pd.DataFrame) -> None:  # pragma: no cover - trivial
        logger.debug("No repository configured; skipping event persistence")


def register_callbacks(app, df, repository=None) -> None:
    """Register event related callbacks on the given Dash ``app``."""
    logger.info("Registering event callbacks")
    repository = repository or _NullEventRepository()

    @app.callback(
        Output("overflow-box", "className"),
        Output("overflow-toggle", "children"),
        Input("overflow-toggle", "n_clicks"),
        State("overflow-date", "data"),
        prevent_initial_call=True,
    )
    def toggle_overflow(n_clicks: int, start_date_str: str) -> Tuple[str, str]:
        """Toggle visibility of the overflow list for the selected week."""
        logger.debug(
            "Overflow toggle received %s click(s) for %s", n_clicks, start_date_str
        )

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = start_date + timedelta(days=6)
            is_open = n_clicks % 2 == 1

            box_class = "overflow-box-expand show" if is_open else "overflow-box-expand"

            date_range = (
                f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
            )
            button_text = (
                f"\U0001f300 Hide Ongoing Events for {date_range}"
                if is_open
                else f"\U0001f300 Show Ongoing Events for {date_range}"
            )

            logger.debug(
                "Overflow toggle state open %s with class %s", is_open, box_class
            )
            return box_class, button_text

        except Exception as e:
            logger.error("toggle_overflow callback failed: %s", e, exc_info=True)
            raise

    @app.callback(
        Output("event-modal", "style"),
        Output("event-modal", "className"),
        Output("event-modal-body", "children"),
        Output("event-edit-form-container", "children", allow_duplicate=True),
        Output("event-edit-footer", "open", allow_duplicate=True),
        Output("event-edit-context", "data"),
        Output("close-timer", "n_intervals"),
        Output("close-timer", "disabled"),
        Output("day-modal", "style"),
        Output("day-modal", "className"),
        Output("day-modal-body", "children"),
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
        State("event-modal", "className"),
        prevent_initial_call=True,
    )
    def show_event_modal(
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
        week_offset: int,
        screen_width: int,
        selected_casinos: list[str] | None,
        event_modal_class: str | None = None,
    ) -> tuple[Any, ...]:
        """Handle modal open and close events.

        Unused parameters prefixed with an underscore are included solely so the
        callback fires when those inputs change.
        """
        start_time = time.time()
        logger.debug("show_event_modal callback triggered")

        def _normalize_pattern_id(raw_id: Any) -> Any:
            """Return pattern IDs parsed from Dash string forms into dicts."""
            if isinstance(raw_id, str):
                parsed_id = None
                try:
                    parsed_id = json.loads(raw_id)
                except json.JSONDecodeError:
                    try:
                        parsed_id = ast.literal_eval(raw_id)
                    except (ValueError, SyntaxError):
                        logger.debug("Unable to parse pattern ID string: %s", raw_id)
                if isinstance(parsed_id, dict):
                    return parsed_id
            return raw_id

        try:
            ctx = dash.callback_context
            triggered_id = _normalize_pattern_id(ctx.triggered_id)
            logger.debug("Trigger source: %s", triggered_id)

            # Note: We intentionally don't parse or use the triggered property name
            # here; the callback logic keys off component IDs and timestamps.

            def _lookup_click_value(target_id: Any, position: int) -> Any:
                """Return a stored value for a pattern-matched component."""

                normalized_target = _normalize_pattern_id(target_id)
                try:
                    inputs = ctx.inputs_list[position]
                except (
                    AttributeError,
                    IndexError,
                ):  # pragma: no cover - dash internals
                    inputs = None

                if inputs:
                    for item in inputs:
                        try:
                            item_id = _normalize_pattern_id(item.get("id"))
                            if item_id == normalized_target:
                                return item.get("value")
                        except AttributeError:
                            continue

                try:
                    last_trigger = ctx.triggered[-1]
                    comp_id = _normalize_pattern_id(last_trigger.get("id"))
                    if comp_id == normalized_target:
                        return last_trigger.get("value")
                    return ctx.triggered[0]["value"] if ctx.triggered else None
                except (IndexError, KeyError, TypeError, AttributeError):
                    return None

            if triggered_id == "close-timer":
                logger.debug("Closing modal via timer")
                modal_class = event_modal_class or ""
                if "closing" not in modal_class:
                    logger.debug(
                        "Timer fired while modal class was %s; disabling without closing",
                        modal_class,
                    )
                    return (
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        0,
                        True,
                        no_update,
                        no_update,
                        no_update,
                    )

                return (
                    {"display": "none"},
                    "modal",
                    "",
                    no_update,
                    False,
                    None,
                    0,
                    True,
                    no_update,
                    no_update,
                    no_update,
                )

            if triggered_id == "close-modal":
                logger.debug("Closing event modal")
                # Close immediately to ensure click layer is removed
                reopen_day = bool(event_modal_class and "from-day" in event_modal_class)
                return (
                    {"display": "none"},
                    "modal closing",
                    no_update,
                    no_update,
                    False,
                    None,
                    0,
                    False,
                    {} if reopen_day else no_update,
                    "modal show" if reopen_day else no_update,
                    no_update,
                )

            if triggered_id == "close-day-modal":
                logger.debug("Closing day modal")
                # Hide the day modal but keep its children so the catcher ID exists
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    {"display": "none"},
                    "modal",
                    no_update,
                )

            def _resolve_click_metadata(
                component_id: dict[str, Any] | None,
                known_ids: list[dict[str, Any]] | None,
                click_values: list[int] | None,
                timestamps: list[int | None] | None,
            ) -> tuple[int | None, int | None]:
                if not component_id or not known_ids:
                    return None, None

                match_index: int | None = None
                for i, candidate in enumerate(known_ids):
                    if candidate == component_id:
                        match_index = i
                        break

                if match_index is None:
                    return None, None

                resolved_click: int | None = None
                resolved_timestamp: int | None = None

                if click_values and len(click_values) > match_index:
                    resolved_click = click_values[match_index]

                if timestamps and len(timestamps) > match_index:
                    resolved_timestamp = timestamps[match_index]

                return resolved_click, resolved_timestamp

            if isinstance(triggered_id, dict) and triggered_id.get("type") in (
                "grid-event",
            ):
                logger.debug("Grid event clicked: %s", triggered_id)

                grid_timestamps = (
                    _grid_click_timestamps_state or _grid_click_timestamps_input
                )
                triggered_n, timestamp_value = _resolve_click_metadata(
                    triggered_id,
                    _grid_click_ids,
                    _grid_clicks,
                    grid_timestamps,
                )

                if triggered_n is None:
                    try:
                        triggered_n = (
                            ctx.triggered[0]["value"] if ctx.triggered else None
                        )
                    except (IndexError, KeyError, TypeError):
                        triggered_n = None

                if timestamp_value is None:
                    try:
                        prop_id = ctx.triggered[0]["prop_id"]
                    except (IndexError, KeyError, TypeError):
                        prop_id = None
                    else:
                        timestamp_key = prop_id.replace(
                            ".n_clicks", ".n_clicks_timestamp"
                        )
                        timestamp_value = (
                            ctx.states.get(timestamp_key)
                            if hasattr(ctx, "states")
                            else None
                        )

                if triggered_n is None or (triggered_n == 0 and not timestamp_value):
                    logger.debug("No triggered value, preventing update")
                    raise dash.exceptions.PreventUpdate

                idx = triggered_id.get("index")

                if idx is None or idx not in df.index:
                    logger.warning("Invalid event index: %s", idx)
                    return (
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                    )

                row = df.loc[idx]
                event_name = (
                    row["EventName"] if "EventName" in row.index else "Unknown Event"
                )
                logger.info("Opening event modal for %s", event_name)
                color_palette = get_color()
                casino_colors = resolve_casino_color(
                    row["Casino"], palette=color_palette
                )
                form_defaults = event_editing.build_form_defaults(row)
                body_children, form_component = (
                    event_editing.build_event_modal_children(row, form_defaults)
                )
                context_payload = {
                    "index": idx,
                    "form": form_defaults,
                    "values": row.to_dict(),
                }
                style = {
                    "--bg": casino_colors["bg"],
                    "--fg": casino_colors["text"],
                    "--bg-dark": casino_colors["bg_dark"],
                    "--fg-dark": casino_colors["text_dark"],
                }
                return (
                    style,
                    "modal show",
                    body_children,
                    form_component,
                    False,
                    context_payload,
                    0,
                    True,
                    {"display": "none"},
                    "modal",
                    no_update,
                )

            if (
                isinstance(triggered_id, dict)
                and triggered_id.get("type") == "day-column"
            ):
                logger.debug("Day column clicked: %s", triggered_id)

                triggered_n, timestamp_value = _resolve_click_metadata(
                    triggered_id,
                    _day_column_ids,
                    _day_column_clicks,
                    _day_column_timestamps,
                )

                if triggered_n is None:
                    try:
                        triggered_n = (
                            ctx.triggered[0]["value"] if ctx.triggered else None
                        )
                    except (IndexError, KeyError, TypeError):
                        triggered_n = None

                if timestamp_value is None:
                    try:
                        prop_id = ctx.triggered[0]["prop_id"]
                    except (IndexError, KeyError, TypeError):
                        prop_id = None
                    else:
                        timestamp_key = prop_id.replace(
                            ".n_clicks", ".n_clicks_timestamp"
                        )
                        timestamp_value = (
                            ctx.states.get(timestamp_key)
                            if hasattr(ctx, "states")
                            else None
                        )

                if triggered_n is None or (triggered_n == 0 and not timestamp_value):
                    logger.debug("No triggered value for day column, preventing update")
                    raise dash.exceptions.PreventUpdate

                date_str = triggered_id.get("index")
                if not date_str:
                    logger.warning("No date string provided for day column click")
                    return (
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                    )

                clicked_date = to_naive_utc(datetime.strptime(date_str, "%Y-%m-%d"))
                logger.info(
                    "Opening day modal for %s", clicked_date.strftime("%Y-%m-%d")
                )

                filtered = (
                    df[df["Casino"].isin(selected_casinos)] if selected_casinos else df
                )
                logger.debug(
                    "Filtered events to %d items based on selected casinos",
                    len(filtered),
                )

                title_text, grid_children, figure, height_px = (
                    day_charts.generate_day_view_parts(
                        filtered, clicked_date, get_color, screen_width
                    )
                )
                day_modal_children = html.Div(
                    id="day-modal-content-container",
                    className="base-padding",
                    children=[
                        html.H2(
                            id="day-modal-title",
                            className="day-label day-modal-title",
                            children=title_text,
                        ),
                        html.Div(
                            id="day-grid-wrapper",
                            style={"position": "relative"},
                            children=[
                                html.Div(id="day-grid-content", children=grid_children),
                                dcc.Graph(
                                    id="day-event-catcher",
                                    className="day-event-catcher",
                                    figure=figure,
                                    config={"displayModeBar": False},
                                    style={
                                        "height": f"{height_px}px",
                                        "pointerEvents": "auto",
                                    },
                                ),
                            ],
                        ),
                    ],
                )

                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    {},
                    "modal show",
                    day_modal_children,
                )

            click_data = None
            if triggered_id == "day-event-catcher":
                click_data = day_click

            if click_data and "points" in click_data and click_data["points"]:
                logger.debug("Processing day-event-catcher click data")
                try:
                    data = click_data["points"][0].get("customdata", [None])[0]
                except (IndexError, KeyError, TypeError) as e:
                    logger.warning("Error accessing click data: %s", e)
                    data = None
                if data and data.get("type") == "day_click":
                    day_index = data.get("day_index")
                    if day_index is None:
                        logger.warning("Day index is None in click data")
                        return (
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                        )

                    today = datetime.utcnow()
                    current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
                    week_start = current_sunday + timedelta(weeks=week_offset)
                    clicked_date = week_start + timedelta(days=day_index)

                    logger.info(
                        "Opening day modal for index %s on %s",
                        day_index,
                        clicked_date.strftime("%Y-%m-%d"),
                    )

                    filtered = (
                        df[df["Casino"].isin(selected_casinos)]
                        if selected_casinos
                        else df
                    )
                    title_text, grid_children, figure, height_px = (
                        day_charts.generate_day_view_parts(
                            filtered, clicked_date, get_color, screen_width
                        )
                    )
                    day_modal_children = html.Div(
                        id="day-modal-content-container",
                        className="base-padding",
                        children=[
                            html.H2(
                                id="day-modal-title",
                                className="day-label day-modal-title",
                                children=title_text,
                            ),
                            html.Div(
                                id="day-grid-wrapper",
                                style={"position": "relative"},
                                children=[
                                    html.Div(
                                        id="day-grid-content", children=grid_children
                                    ),
                                    dcc.Graph(
                                        id="day-event-catcher",
                                        className="day-event-catcher",
                                        figure=figure,
                                        config={"displayModeBar": False},
                                        style={
                                            "height": f"{height_px}px",
                                            "pointerEvents": "auto",
                                        },
                                    ),
                                ],
                            ),
                        ],
                    )

                    return (
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        {},
                        "modal show",
                        day_modal_children,
                    )

                if data and all(
                    k in data
                    for k in [
                        "EventName",
                        "Casino",
                        "OfferType",
                        "StartDate",
                        "EndDate",
                        "Offer",
                    ]
                ):
                    event_name = data.get("EventName", "Unknown Event")
                    logger.info("Opening event modal for %s", event_name)
                    palette = get_color()
                    casino_colors = resolve_casino_color(
                        data.get("Casino", ""), palette=palette
                    )
                    style = {
                        "--bg": casino_colors["bg"],
                        "--fg": casino_colors["text"],
                        "--bg-dark": casino_colors["bg_dark"],
                        "--fg-dark": casino_colors["text_dark"],
                    }

                    day_context_payload: dict[str, Any] | None = None
                    day_body_children: list[Any]

                    try:
                        match_idx = None
                        start_candidate = data.get("StartDate")
                        end_candidate = data.get("EndDate")
                        if start_candidate and end_candidate:
                            normalized_start = to_naive_utc(
                                pd.to_datetime(start_candidate).to_pydatetime()
                            )
                            normalized_end = to_naive_utc(
                                pd.to_datetime(end_candidate).to_pydatetime()
                            )
                            matches = df[
                                (df["EventName"] == data.get("EventName"))
                                & (df["Casino"] == data.get("Casino"))
                                & (df["StartDate"] == normalized_start)
                                & (df["EndDate"] == normalized_end)
                            ]
                            if not matches.empty:
                                match_idx = matches.index[0]
                        if match_idx is not None:
                            logger.debug(
                                "Matched day view event to index %s", match_idx
                            )
                            row = df.loc[match_idx]
                            form_defaults = event_editing.build_form_defaults(row)
                            day_body_children, form_component = (
                                event_editing.build_event_modal_children(
                                    row, form_defaults
                                )
                            )
                            day_context_payload = {
                                "index": match_idx,
                                "form": form_defaults,
                                "values": row.to_dict(),
                            }
                        else:
                            logger.debug(
                                "Unable to match day view event to DataFrame index; using read-only data"
                            )
                            row = pd.Series(data)
                            day_body_children, form_component = (
                                event_editing.build_event_modal_children(
                                    row, event_editing.build_form_defaults(row)
                                )
                            )
                    except Exception as err:  # pragma: no cover - defensive logging
                        logger.warning(
                            "Failed to prepare editable modal from day view data: %s",
                            err,
                        )
                        row = pd.Series(data)
                        day_body_children, form_component = (
                            event_editing.build_event_modal_children(
                                row, event_editing.build_form_defaults(row)
                            )
                        )
                        day_context_payload = None

                    return (
                        style,
                        "modal show from-day",
                        day_body_children,
                        form_component,
                        False,
                        day_context_payload,
                        0,
                        True,
                        {"display": "none"},
                        "modal",
                        no_update,
                    )

            logger.debug("No valid trigger found, preventing update")
            end_time = time.time()
            logger.debug(
                "show_event_modal callback finished in %.3f seconds (PreventUpdate)",
                end_time - start_time,
            )
            raise dash.exceptions.PreventUpdate

        except dash.exceptions.PreventUpdate:
            # PreventUpdate is expected behavior, not an error - just re-raise it
            end_time = time.time()
            logger.debug(
                "show_event_modal callback finished in %.3f seconds (PreventUpdate)",
                end_time - start_time,
            )
            raise
        except Exception as e:
            logger.error("show_event_modal callback failed: %s", e, exc_info=True)
            # Log performance even on error
            end_time = time.time()
            logger.debug(
                "show_event_modal callback finished in %.3f seconds (error)",
                end_time - start_time,
            )
            raise

    @app.callback(
        Output("event-modal-body", "children", allow_duplicate=True),
        Output("event-edit-form-container", "children", allow_duplicate=True),
        Output("event-edit-context", "data", allow_duplicate=True),
        Output("event-edit-footer", "open", allow_duplicate=True),
        Output("event-save-status", "children"),
        Output("event-save-status", "className"),
        Output("event-data-refresh", "data"),
        Input("event-save-button", "n_clicks"),
        State("event-edit-context", "data"),
        State("event-edit-eventname", "value"),
        State("event-edit-offertype", "value"),
        State("event-edit-offer", "value"),
        State("event-edit-startdate", "value"),
        State("event-edit-enddate", "value"),
        prevent_initial_call=True,
    )
    def persist_event_changes(
        n_clicks: int,
        context_data: dict[str, Any] | None,
        name: str | None,
        offer_type: str | None,
        offer: str | None,
        start_value: str | None,
        end_value: str | None,
    ) -> tuple[Any, ...]:
        """Persist edited event information to disk."""

        if not n_clicks:
            raise dash.exceptions.PreventUpdate

        context_payload = dict(context_data or {})
        form_values = {
            "EventName": name or "",
            "OfferType": offer_type or "",
            "Offer": offer or "",
            "StartDate": start_value or "",
            "EndDate": end_value or "",
        }
        context_payload["form"] = form_values

        event_index = context_payload.get("index")
        if event_index is None:
            logger.warning("Save requested without a selected event")
            return (
                no_update,
                no_update,
                context_payload or None,
                True,
                "Select an event from the calendar before saving changes.",
                "event-save-status error",
                no_update,
            )

        if event_index not in df.index:
            logger.warning("Event index %s no longer available", event_index)
            return (
                no_update,
                no_update,
                context_payload,
                True,
                "The selected event is no longer available.",
                "event-save-status error",
                no_update,
            )

        normalized, errors = event_editing.normalize_event_update(form_values)

        if errors:
            logger.info(
                "Validation failed when saving event %s: %s", event_index, errors
            )
            row = df.loc[event_index]
            body_children, form_component = event_editing.build_event_modal_children(
                row, form_values
            )
            message = html.Ul([html.Li(err) for err in errors])
            return (
                body_children,
                form_component,
                context_payload,
                True,
                message,
                "event-save-status error",
                no_update,
            )

        row = df.loc[event_index]
        logger.debug("Applying updates to event %s", event_index)

        for column, value in normalized.items():
            if column not in df.columns:
                df[column] = pd.NA
            df.at[event_index, column] = value

        # Ensure optional text fields reflect empty strings rather than NaN
        for column in form_values:
            if column not in normalized:
                df.at[event_index, column] = form_values[column]

        try:
            repository.save_events(df)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Failed to save updated events: %s", exc, exc_info=True)
            body_children, form_component = event_editing.build_event_modal_children(
                row, form_values
            )
            return (
                body_children,
                form_component,
                context_payload,
                True,
                "An unexpected error occurred while saving. Please try again.",
                "event-save-status error",
                no_update,
            )

        updated_row = df.loc[event_index]
        form_defaults = event_editing.build_form_defaults(updated_row)
        context_payload = {
            "index": event_index,
            "form": form_defaults,
            "values": updated_row.to_dict(),
        }
        body_children, form_component = event_editing.build_event_modal_children(
            updated_row, form_defaults
        )
        refresh_token = str(uuid4())

        logger.info("Event %s updated and saved to CSV", event_index)

        return (
            body_children,
            form_component,
            context_payload,
            False,
            "Changes saved successfully.",
            "event-save-status success",
            refresh_token,
        )

    logger.info("Event callbacks ready")
