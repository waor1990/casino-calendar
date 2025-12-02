# Data Files

This directory contains data files used by the Casino Calendar application.

## Files

- **events.json**: REST API-backed event store persisted by `api/event_api.py`
- **casino_events.csv**: Legacy CSV used by older tooling; superseded by `events.json`
- **casino_colors.json**: Color scheme definitions for each casino
- **default_colors.json**: Fallback color scheme
- **hotel_book_sites.json**: Hotel booking URLs for each casino (used for the hotel booking feature)
- **offer_keywords.json**: Keywords used for categorizing event offers
- **offer_type_emojis.json**: Emoji mappings for different offer types

## Hotel Booking Sites

The `hotel_book_sites.json` file contains hotel booking URLs for casinos. When a user selects a casino from the legend, if a booking URL is available, a "Hotel Booking" link will appear below the legend.

**Format:**

```json
{
  "Casino Name": "https://booking-url.com",
  "Another Casino": "N/A"
}
```

- Use `"N/A"` for casinos that don't have hotel booking available
- The hotel booking link only appears when exactly one casino is selected
- Links open in a new tab/window
