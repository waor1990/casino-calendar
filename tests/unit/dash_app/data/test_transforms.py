import pandas as pd

from casino_calendar.dash_app.data.transforms import (categorize_offer_type,
                                                      categorize_offer_types)
from casino_calendar.services.config_cache import clear_cache


def test_free_play_prize_phrases_classify_as_drawing() -> None:
    clear_cache()
    result = categorize_offer_type(
        event_name=None, offer="Win up to $500 in Free Play prizes"
    )
    assert result == "Drawings"


def test_standard_free_play_remains_free_play() -> None:
    clear_cache()
    df = pd.DataFrame(
        {
            "EventName": [None, None],
            "Offer": ["Enter to win $1,000 in free play", "Enjoy $25 Free Play"],
        }
    )

    category = categorize_offer_types(df)

    assert category.iloc[0] == "Drawings"
    assert category.iloc[1] == "Free-Play"
