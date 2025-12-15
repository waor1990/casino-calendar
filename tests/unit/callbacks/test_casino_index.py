import pandas as pd
from casino_calendar.dash_app.callbacks import register_callbacks
from dash import Dash


class DummyCtx:
    def __init__(self, triggered_id):
        self.triggered_id = triggered_id
        self.triggered = (
            [{"prop_id": f"{triggered_id}.n_clicks", "value": 1}]
            if triggered_id
            else []
        )


def test_casino_index_modal_toggle(monkeypatch, casino):
    df = pd.DataFrame({"Casino": [casino], "OfferType": ["Giveaway"]})
    app = Dash(__name__)
    register_callbacks(app, df)

    key = next(key for key in app.callback_map if "casino-index-modal.className" in key)
    callback = app.callback_map[key]["callback"].__wrapped__

    monkeypatch.setattr(
        "dash.callback_context", DummyCtx("open-casino-index-modal"), raising=False
    )
    class_name, style = callback(1, 0)
    assert class_name == "modal show"
    assert style == {}

    monkeypatch.setattr(
        "dash.callback_context", DummyCtx("close-casino-index-modal"), raising=False
    )
    class_name, style = callback(1, 1)
    assert class_name == "modal"
    assert style == {"display": "none"}
