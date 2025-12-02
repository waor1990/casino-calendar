"""REST API backed repository for Casino Calendar events."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests
from casino_calendar.dash_app.data.transforms import (
    categorize_offer_types,
    to_naive_utc,
)
from casino_calendar.logging.config import setup_logger

logger = setup_logger(__name__)


class APIEventRepository:
    """Repository that interacts with the event REST API."""

    def __init__(self, base_url: str = "http://localhost:5001") -> None:
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        logger.debug("Sending %s request to %s", method.upper(), url)
        response = requests.request(method=method, url=url, timeout=10, **kwargs)
        response.raise_for_status()
        if not response.content:
            return None
        return response.json()

    def get_events(self) -> pd.DataFrame:
        """Fetch events from the API and return them as a DataFrame."""

        data = self._request("get", "/events") or []
        df = pd.DataFrame(data)
        if df.empty:
            return df

        for column in ["StartDate", "EndDate"]:
            df[column] = pd.to_datetime(df[column], errors="coerce")
            df[column] = df[column].map(to_naive_utc)

        if "OfferType" not in df.columns:
            df["OfferType"] = categorize_offer_types(df)
        else:
            df["OfferType"] = df["OfferType"].fillna("")

        return df

    def save_event(self, event_dict: dict[str, Any]) -> dict[str, Any]:
        """Create a new event via POST."""

        return self._request("post", "/events", json=event_dict)

    def update_event(self, event_id: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        """Update an existing event via PUT."""

        return self._request("put", f"/events/{event_id}", json=event_dict)
