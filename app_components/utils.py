from datetime import datetime, timedelta
from pytz import timezone
from typing import Tuple

PDT = timezone('America/Los_Angeles')

def get_dynamic_sizes(screen_width):
    if screen_width < 480:
        font_sizes = {
            "h1": "1.5rem",
            "legend_title": "1.3rem",
            "legend": "1rem",
            "button": "2.5rem",
            "event_block": "0.8rem",
            "overflow": "0.9rem",
        }
        padding_sizes = {
            "header_padding": "8px 10px",
            "button_padding": "4px 6px",
            "week_gap": "10px",
            "legend_gap": "2px",
            "section_margin": "10px",
        }
    elif screen_width < 768:
        font_sizes = {
            "h1": "2rem",
            "legend_title": "1.5rem",
            "legend": "1.2rem",
            "button": "2.6rem",
            "event_block": "0.9rem",
            "overflow": "1rem",
        }
        padding_sizes = {
            "header_padding": "10px 15px",
            "button_padding": "4px 6px",
            "week_gap": "15px",
            "legend_gap": "8px",
            "section_margin": "15px",
        }
    else:
        font_sizes = {
            "h1": "2.5rem",
            "legend_title": "1.9rem",
            "legend": "1.5rem",
            "button": "2.7rem",
            "event_block": "1rem",
            "overflow": "1.2rem",
        }
        padding_sizes = {
            "header_padding": "15px 20px",
            "button_padding": "4px 6px",
            "week_gap": "20px",
            "legend_gap": "10px",
            "section_margin": "20px",
        }
    return font_sizes, padding_sizes

def get_week_range(clicked_date: datetime) -> Tuple[datetime, datetime]:
    week_start = clicked_date - timedelta(days=(clicked_date.weekday() + 1) % 7)
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0), week_start + timedelta(days=7)

