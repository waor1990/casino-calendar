# Project Structure Documentation

This document outlines the Casino Calendar repository. The layout emphasises a clear separation between core application code, assets, configuration, and automation tooling.

## Organisation Philosophy

- **Root directory** holds entry points, high-level docs, and convenience launchers only.
- **Package-first Python code** lives under `src/casino_calendar/` to mirror production imports.
- **Assets and data** are grouped by lifecycle (`assets/styles/` vs. generated `assets/dist/`; raw CSV vs. lookup caches).
- **Tooling** is grouped by runtime (`scripts/python/`, `scripts/shell/`, etc.).
- **Legacy materials** reside in `docs/legacy/` to keep the primary docs focused on the current architecture.

## Root Directory Quick Reference

- `app.py` – Imports `create_dash_app()` and exposes `server` for Gunicorn.
- `wsgi.py` – Optional WSGI entry point.
- `deploy/` – Deployment descriptors (`Procfile`, `render.yaml`, `gunicorn.conf.py`).
- `package.json` / `package-lock.json` – Node toolchain for Sass and Stylelint.
- Convenience launchers: `setup.bat`, `run.bat`, `cleanup.bat`.

## Key Directories

### `src/casino_calendar/`

- `dash_app/app.py` – Dash factory returning the app and server, including cache warming.
- `dash_app/callbacks/` – Modular callback handlers for events, filters, navigation, and theming.
- `dash_app/data/` – CSV loader, repository wrapper, and transforms for dataset normalisation.
- `dash_app/layout/` – Layout factory (`root.py`), CSS grid helpers (`week_grid.py`), and reusable component builders under `layout/components/`.
- `dash_app/services/` – Layout/callback utilities (timezone helpers, modal formatting, lookup helpers).
- `dash_app/visualization/` – Plotly chart builders used by the day modal overlays.
- `logging/` – Logging configuration (`config.py`) and rotation utilities (`rotation.py`).
- `services/` – Application-wide services (config cache, colour palette resolution, data parsing).
- `settings.py` – Environment helpers and canonical path definitions (e.g., `DATA_DIR`).

### `assets/`

- `styles/index.scss` – Sass entry point importing partials from `styles/partials/`.
- `dist/style.css` – Compiled CSS (always generated; never edit directly).
- `scripts/theme-toggle.js` – Client-side theme switcher for Dash.

### `data/`

- `raw/casino_events.csv` – Primary dataset.
- `lookups/` – JSON lookup tables (casino colours, default palette, offer keywords, hotel metadata, etc.).
- `cache/` – Placeholder for runtime caches (kept empty in version control).

### `config/`

- `formatting/pyproject.toml` – Black configuration.
- `formatting/.isort.cfg` – isort profile aligned to Black.
- `linting/.flake8` – Flake8 configuration.
- `linting/.stylelintrc.json` – Stylelint rules for Sass.
- `typing/mypy.ini` – Mypy configuration.

### `scripts/`

- `python/` – Python utilities (`cleanup_logs.py`, `verify_requirements.py`, etc.).
- `shell/` – Bash helpers (`setup.sh`, `test.sh`).
- `node/` – Node automation tools (`append-casino-event.mjs`, `trim-old-casino-events.mjs`, `verify-package-json.mjs`).
- `windows/` – Windows batch launchers mirroring the Python helpers.

### `tests/`

- `unit/` – Unit tests grouped by domain (callbacks, layout, services, visualization, theme).
- `integration/` – Higher-level Dash interactions; visual tests marked to skip when dependencies are missing.
- `e2e/` – Placeholders for Percy/Selenium suites.

### Documentation

- `docs/README.md` – Documentation index.
- `docs/guides/handoff.md` – Operational handoff notes and feature summary.
- `docs/architecture/logging_system.md` – Logging architecture overview with environment variable reference.
- `docs/legacy/` – Historical notes and archived automation scripts.

## Legacy Material

Earlier directories such as `app_components/`, `utils/`, and `tools/` have been consolidated into the package and runtime-specific script directories. Historical versions can be found under `docs/legacy/` if needed for reference.
