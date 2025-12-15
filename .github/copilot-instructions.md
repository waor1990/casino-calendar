# Casino Calendar - Copilot Instructions

This Dash web application renders casino events on a responsive calendar. The stack targets Python 3.11 and Node 22 (tested with Node 22.9.0).

## Architecture Overview
- **`app.py` / `wsgi.py`** – Entry points that instantiate the Dash app via the package factory.
- **`src/casino_calendar/`** – Primary Python package:
  - **`dash_app/app.py`** – `create_dash_app()` factory returning the Dash application and Flask server.
  - **`dash_app/callbacks/`** – Domain-specific callback modules (events, filters, navigation, theme) aggregated in `callbacks/__init__.py`.
  - **`dash_app/data/`** – CSV loader (`loader.py`), repository wrapper, and vectorised transforms.
  - **`dash_app/layout/`** – Layout factory plus component helpers under `layout/components/`.
  - **`dash_app/services/`** – Helpers used by callbacks/layout (timezone conversions, offer formatting, etc.).
  - **`dash_app/visualization/`** – Plotly chart builders powering the day modal and overlays.
  - **`logging/`** – Centralised logging config (`config.py`) and rotation helpers.
  - **`services/`** – Shared services (config cache, colours, data parsing utilities).
- **`assets/`** – Static assets auto-loaded by Dash:
  - Source Sass lives under `assets/styles/` with partials in `styles/partials/`.
  - Compiled CSS is written to `assets/dist/style.css`.
  - Client-side helpers (e.g., theme toggle) live in `assets/scripts/`.
- **`config/`** – Tooling configuration split into `formatting/`, `linting/`, and `typing/`.
- **`data/`** – `raw/` CSVs plus lookup JSON files consumed by the services layer.
- **`scripts/`** – Utility scripts grouped by runtime (`python/`, `shell/`, `node/`, `windows/`).
- **`deploy/`** – Procfile, Render configuration, and Gunicorn settings.

## Key Patterns
### Data Flow
1. `load_event_data()` in `dash_app/data/loader.py` loads `data/raw/casino_events.csv` and normalises timestamps.
2. Transforms in `dash_app/data/transforms.py` categorise offers and perform vectorised cleanup.
3. `create_layout()` in `dash_app/layout/root.py` builds the component tree.
4. Callbacks from `dash_app/callbacks/` drive interactivity.

### Callback Organisation
- `callbacks/events.py` – Modal dialog behaviour and day-event interactions.
- `callbacks/filters.py` – Casino filters, responsive sizing, and hotel links.
- `callbacks/navigation.py` – Home button redirects and week navigation persistence.
- `callbacks/theme.py` – Theme toggle and clientside application.

### Logging
- Use `casino_calendar.logging.config.setup_logger()` in every module.
- `LOG_LEVEL` and `LOG_FILE` environment variables control verbosity and file output.
- Rotation helpers live in `casino_calendar.logging.rotation` and are wired automatically by `setup_logger`.

## Development Workflow
### Windows
```cmd
scripts\windows\setup.bat           # Create venv, install dependencies, build CSS
scripts\windows\run_direct.bat      # Build CSS and launch the Dash app
scripts\windows\cleanup_logs.bat    # Trim rotated log files
### macOS / Linux
scripts/shell/setup.sh               # Install Python and Node dependencies
npm run build:css                    # Compile assets/styles/index.scss to assets/dist/style.css
scripts/shell/test.sh                # Run linters and tests
- Use `npm run watch:css` for development; run `npm run build:css` before committing.
- Variables and mixins live in `_variables.scss` and `_mixins.scss`.
2. Rebuild CSS via `npm run build:css` (emits `assets/dist/style.css`).
- Rotating logs live under `logs/`; archive helpers live in `scripts/python/cleanup_logs.py` and `scripts/windows/cleanup_logs.bat`.

## Commit Formatting
- Follow Conventional Commit syntax: `<type>(<scope>): <subject>` with lower-case subjects.
- Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `merge`, `revert`.
- Require a non-empty scope such as `app`, `layout`, `styles`, `data`, `scripts`, `tests`, `docs`, or `infra` (see `commitlint.config.js`).
- Keep subjects brief (≤72 characters) and omit trailing punctuation.
```

### CSS / Sass

- **Never edit `assets/dist/style.css` directly.**
- Author styles in `assets/styles/index.scss` and partials under `assets/styles/partials/`.
- Use `npm run watch:css` for development, `npm run build:css` before commit.
- Variables/mixins live in `_variables.scss` and `_mixins.scss`.

### Testing & Quality

- Execute `scripts/shell/test.sh` prior to commits (runs Black, isort, flake8, pytest, CSS lint).
- CSS lint uses Stylelint config at `config/linting/.stylelintrc.json`.
- Pytest suites live under `tests/unit`, `tests/integration`, and `tests/e2e`.

### VS Code Tasks

- "Run Casino Calendar App" – launches Dash via the factory with logging.
- "Run Tests" – executes pytest with coverage.
- "Install Dependencies" – installs Python requirements and Node packages.

## Project Conventions

- Prefer package imports from `casino_calendar...` rather than relative paths outside each module.
- For shared helpers use `casino_calendar.services` and `casino_calendar.dash_app.services`.
- Honour type hints in public interfaces to keep mypy happy.

## Common Operations

### Adding a Callback

1. Implement logic inside the appropriate module under `dash_app/callbacks/`.
2. Expose the callback via the module-level `register_callbacks()`.
3. Import and wire it in `dash_app/callbacks/__init__.py`.

### Updating Data Schema

1. Edit `data/raw/casino_events.csv` (or provide new data sources).
2. Update parsing in `dash_app/data/loader.py` and transforms in `dash_app/data/transforms.py`.
3. Adjust layout/callback expectations and corresponding tests.

### Styling Changes

1. Modify SCSS in `assets/styles/partials/` or `index.scss`.
2. Rebuild CSS via `npm run build:css` (automatically emits `assets/dist/style.css`).
3. Verify responsive behaviour across breakpoints.

### Logging Checks

- Use `LOG_LEVEL=DEBUG python app.py` for verbose output.
- Check rotating logs under `logs/`; archive helpers live in `scripts/python/cleanup_logs.py` and `scripts/windows/cleanup_logs.bat`.
