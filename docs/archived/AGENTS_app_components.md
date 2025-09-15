# AI Agent Instructions for `app_components`

This directory contains the Python modules for the Dash application.

**See root `AGENTS.md` and `.github/copilot-instructions.md` for comprehensive guidelines.**

## Module Structure

- `layout.py` - Main UI layout generation using Dash components
- `data.py` - CSV data loading and processing with pandas
- `logging_config.py` - Centralized logging setup and configuration
- `callbacks/` - Event handlers split by domain (events, filters, theme)
- `utils.py` - Utility functions for data processing
- `plotting.py` - Chart generation helpers
- `week_grid_layout.py` - Weekly calendar grid layout components

## Key Patterns

### Data Processing

- Load events from CSV with `load_event_data()` in `data.py`
- All datetime handling uses pandas with timezone conversion
- Events have: EventName, Casino, Location, Offer, StartDate, EndDate

### Callback Registration

- Each callback module has a `register_callbacks(app, df)` function
- Centrally registered in `callbacks/__init__.py`
- Split by domain: events (modals), filters (casino/date), theme (UI)

### Logging

- Use `setup_logger(__name__)` in all modules
- Structured logging with context for debugging
- Performance logging for data operations

## Development Guidelines

- Follow the style and tooling described in the repository root `AGENTS.md`
- Keep functions small and focused with type hints and docstrings
- Avoid side effects and prefer returning new values over mutating arguments
- Historical Plotly helpers are documented in `docs/legacy_plotly.md`
- Split out helpers if a file grows beyond roughly 400 lines
- Check syntax before committing:

  ```bash
  python -m py_compile *.py
  ```

## Import Conventions

- Use relative imports within `app_components/`: `from .data import load_event_data`
- Import utilities with full paths: `from utils.colors import get_color`
- Type hints preferred, especially for function signatures

*[End of app_components guidelines]*
