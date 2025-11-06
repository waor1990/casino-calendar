"""Callbacks enabling event editing and persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import dash
import pandas as pd
from dash import ALL, Input, Output, State, dcc, html, no_update

from casino_calendar.logging.config import setup_logger

logger = setup_logger(__name__)

EDITABLE_FIELDS = ["EventName", "Casino", "Location", "Offer", "StartDate", "EndDate"]
DATE_FIELDS = {"StartDate", "EndDate"}


def _stringify_value(field: str, value: Any) -> str:
    """Return a user-friendly string representation for ``value``."""

    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""

    if field in DATE_FIELDS:
        try:
            ts = pd.to_datetime(value)
        except Exception:
            return str(value)
        return ts.strftime("%Y-%m-%d %H:%M")

    if isinstance(value, (datetime, pd.Timestamp)):
        return value.strftime("%Y-%m-%d %H:%M")

    return str(value)


def _build_form_fields(event: dict[str, Any]) -> list[Any]:
    """Return Dash components representing editable fields for ``event``."""

    fields: list[Any] = []
    for field in EDITABLE_FIELDS:
        field_id = {"type": "event-edit-field", "name": field}
        value = _stringify_value(field, event.get(field))

        if field in {"Offer", "Location"}:
            input_control: Any = dcc.Textarea(
                id=field_id,
                value=value,
                className="event-edit-textarea",
                style={"width": "100%"},
            )
        else:
            input_control = dcc.Input(
                id=field_id,
                value=value,
                className="event-edit-input",
                type="text",
            )

        fields.append(
            html.Div(
                [
                    html.Label(field, className="event-edit-label"),
                    input_control,
                ],
                className="event-edit-field",
            )
        )

    return fields


def _normalize_update(field: str, value: Any) -> Any:
    """Return ``value`` coerced to the appropriate representation."""

    if isinstance(value, str):
        value = value.strip()

    if field in DATE_FIELDS:
        if value in ("", None):
            return ""
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            logger.warning("Unable to parse %s date value %r", field, value)
            return value
        return parsed.isoformat()

    return value


def register_callbacks(
    app, df, repository
) -> None:  # noqa: ARG001 - df reserved for future use
    """Register event editing callbacks."""

    if repository is None:
        raise ValueError(
            "An EventRepository instance is required for editing callbacks"
        )

    logger.info("Registering event editing callbacks")

    @app.callback(
        Output("event-edit-mode", "data"),
        Input("event-edit-start", "n_clicks"),
        Input("event-edit-cancel", "n_clicks"),
        Input("event-edit-save", "n_clicks"),
        Input("close-modal", "n_clicks"),
        State("selected-event-data", "data"),
        prevent_initial_call=True,
    )
    def toggle_edit_mode(
        start_clicks, cancel_clicks, save_clicks, close_clicks, selected_event
    ):
        ctx = dash.callback_context
        triggered = getattr(ctx, "triggered_id", None)

        if triggered == "event-edit-start":
            if not selected_event:
                raise dash.exceptions.PreventUpdate
            logger.debug(
                "Entering edit mode for event %s", selected_event.get("EventName")
            )
            return True

        if triggered in {"event-edit-cancel", "event-edit-save", "close-modal"}:
            logger.debug("Exiting edit mode trigger=%s", triggered)
            return False

        raise dash.exceptions.PreventUpdate

    @app.callback(
        Output("event-edit-container", "style"),
        Output("event-edit-form", "children"),
        Input("event-edit-mode", "data"),
        Input("selected-event-data", "data"),
    )
    def update_edit_container(is_editing: bool, selected_event: dict[str, Any] | None):
        if not is_editing or not selected_event:
            return {"display": "none"}, []

        logger.debug("Preparing edit form for row %s", selected_event.get("_row_index"))
        return {"display": "block"}, _build_form_fields(selected_event)

    @app.callback(
        Output("event-edit-start", "disabled"),
        Output("event-edit-start", "style"),
        Input("selected-event-data", "data"),
        Input("event-edit-mode", "data"),
    )
    def update_start_button(selected_event: dict[str, Any] | None, is_editing: bool):
        disabled = selected_event is None
        style = {"display": "none"} if is_editing else {"display": "inline-block"}
        return disabled, style

    @app.callback(
        Output("event-dataset", "data"),
        Output("legacy-event-data", "data"),
        Output("event-edit-status", "children"),
        Output("selected-event-data", "data"),
        Input("event-edit-save", "n_clicks"),
        State({"type": "event-edit-field", "name": ALL}, "value"),
        State({"type": "event-edit-field", "name": ALL}, "id"),
        State("event-dataset", "data"),
        State("selected-event-data", "data"),
        prevent_initial_call=True,
    )
    def persist_event_edits(
        save_clicks,
        field_values,
        field_ids,
        dataset,
        selected_event,
    ):
        if not save_clicks:
            raise dash.exceptions.PreventUpdate

        if not selected_event:
            logger.warning("Save triggered with no selected event")
            raise dash.exceptions.PreventUpdate

        if not isinstance(dataset, list):
            logger.warning("Event dataset unavailable; skipping save")
            raise dash.exceptions.PreventUpdate

        updates: dict[str, Any] = {}
        for value, field_id in zip(field_values, field_ids):
            if not isinstance(field_id, dict):
                continue
            field_name = field_id.get("name")
            if field_name not in EDITABLE_FIELDS:
                continue
            updates[field_name] = _normalize_update(field_name, value)

        if not updates:
            logger.debug("No updates detected; skipping save")
            return no_update, no_update, "No changes to save", no_update

        row_index = selected_event.get("_row_index")
        if row_index is None:
            logger.error("Selected event is missing an index; aborting save")
            raise dash.exceptions.PreventUpdate

        updated_records = []
        updated_selected = None
        for record in dataset:
            if not isinstance(record, dict):
                continue
            if record.get("_row_index") == row_index:
                new_record = {**record, **updates}
                updated_records.append(new_record)
                updated_selected = new_record
            else:
                updated_records.append(record)

        if updated_selected is None:
            logger.error("Could not locate record for row %s", row_index)
            raise dash.exceptions.PreventUpdate

        try:
            repository.save_events(updated_records)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Failed to persist event edits: %s", exc)
            return no_update, no_update, "Failed to save changes", no_update

        logger.info("Event %s updated successfully", updated_selected.get("EventName"))
        return (
            updated_records,
            updated_records,
            "Changes saved successfully",
            updated_selected,
        )

    @app.callback(
        Output("event-edit-status", "children"),
        Input("event-edit-mode", "data"),
        prevent_initial_call=True,
    )
    def clear_status_on_mode_change(is_editing: bool):
        if is_editing:
            return ""
        return no_update


__all__ = ["register_callbacks"]
