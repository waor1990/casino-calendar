# Archived Legacy Utilities

This directory stores historical scripts and utilities that are no longer part of the active Casino Calendar application.

- `deprecated_scripts/import_sanity.py` previously attempted to import modules from the removed `app_components` package. The
  script is preserved for reference only and should not be executed as part of the modern test suite.

Active development should rely on the modules within `src/casino_calendar/` and the automated tests under `tests/`.
