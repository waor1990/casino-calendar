# Data Files

Authoritative CSV and lookup data that drive the Casino Calendar UI.

## Layout

- `raw/casino_events.csv` – Primary dataset. `StartDate`/`EndDate` timestamps are parsed, converted to naive UTC, and an `OfferType` column is derived automatically during load.
- `lookups/`
  - `casino_colors.json` and `default_colors.json` – Brand colour mappings and fallbacks.
  - `offer_keywords.json` and `offer_type_emojis.json` – Keyword groupings and emoji used for offer categorisation.
  - `hotel_book_sites.json` – Booking URLs surfaced in the legend modal when a single casino is selected.
  - `casino_index.json` – Legend metadata (addresses, hours, notes) rendered alongside filters.
- `cache/` – Reserved for generated caches (kept empty in version control).

## Data Update Tips

- Keep CSV headers stable; new columns should be handled in `src/casino_calendar/dash_app/data/transforms.py`.
- Dates must be parseable by pandas (`StartDate`, `EndDate`); invalid rows are logged.
- Preserve JSON indentation and ordering where possible to keep diffs small.
