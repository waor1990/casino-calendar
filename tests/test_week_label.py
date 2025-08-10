import pandas as pd
from app_components.callbacks import register_callbacks
from dash import Dash
from freezegun import freeze_time


@freeze_time("2025-04-15")
def test_week_label_matches_grid():
    app = Dash(__name__)
    register_callbacks(app, pd.DataFrame())
    func = app.callback_map["week-label.children"]["callback"].__wrapped__
    label = func(0)
    assert label == "Events for the Week of April 13 - April 19, 2025"
