# 🎰 Casino Event Calendar

A Dash application that visualizes casino promotions on a responsive weekly calendar. Interactive callbacks power event modals, casino and offer filters, and a hotel booking helper that surfaces links for the selected venue (including when multiple venues are filtered and only one offers booking). The project targets **Python 3.11** and **Node 22**.

---

## ✨ Highlights

- Weekly calendar built with Dash components and CSS grid utilities
- Modal dialogs for day and event detail views with Plotly-powered overlays
- Casino and offer-type filtering backed by Dash stores
- Theme toggle (light/dark) with a floating top-right action button and persisted preference in local storage
- Automatic offer categorisation and colour assignment driven by JSON lookups
- Comprehensive logging with rotation, optional HTTP access log capture, and maintenance utilities

---

## 🧱 Architecture Overview

The repository follows a "src/" layout with a single Python package:

```text
app.py / wsgi.py     # Entrypoints that expose the Dash server
src/casino_calendar/ # Application package
  dash_app/          # Dash factory, callbacks, layout helpers, figures
  logging/           # Logging configuration and rotation helpers
  services/          # Shared services (config cache, colour helpers, parsing)
  settings.py        # Environment handling and shared path constants
assets/              # Sass sources and generated CSS (dist/style.css)
data/                # CSV source data and lookup tables
scripts/             # Python, shell, node, and Windows automation helpers
config/              # Tooling configuration (black, flake8, mypy, stylelint)
docs/                # Architecture guides and operational notes
```

For additional detail see [docs/architecture/project_structure.md](docs/architecture/project_structure.md).

---

## 🧰 Requirements

- Python 3.11 (virtual environment strongly recommended)
- Node.js 22.x (uses Sass CLI and Stylelint)
- npm ≥ 10
- Optional: Google Chrome/Chromedriver for end-to-end tests

Python dependencies are defined in [`requirements.txt`](requirements.txt); the primary runtime stack is Dash, Plotly, Pandas, and python-dotenv.

---

## ⚙️ Installation

### Windows quick start

```cmd
REM Create and activate the virtual environment, install Python/Node deps, compile Sass
scripts\windows\setup.bat

REM Launch the Dash development server
scripts\windows\run_direct.bat
```

Convenience launchers (`setup.bat`, `run.bat`, `run_direct.bat`) proxy to the scripts above.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate

# Install Python requirements
pip install -r requirements.txt

# Install Node dependencies and build CSS assets
npm install
npm run build:css

# Optional quality checks
python scripts/python/check_environment.py  # Validate Python/Node versions
npm run lint:css          # Check Sass formatting
npm run lint:css:fix      # Auto-fix Sass formatting
black .
isort .
flake8

# Launch the Dash development server
python app.py
```

When using `python-dotenv`, environment variables are loaded from `.env` in the project root. See [Environment configuration](#-environment-configuration) for details.

---

## Dependency automation

- Windows: `scripts\windows\setup.bat` checks the venv, compares installed packages to `requirements.txt`, dry-runs pip for conflicts, and installs updates on request; it also validates `package.json` and runs `npm install`.
- Linux/macOS: `bash scripts/shell/setup.sh` upgrades pip, installs Python requirements, installs Node dependencies, and builds CSS. If `core.hooksPath` is set, pre-commit hooks are skipped; run `git config --unset-all core.hooksPath` to enable hooks.
- Any OS: `python scripts/python/verify_requirements.py` checks installed packages against `requirements.txt`; `python scripts/python/check_environment.py --auto-fix` validates Python/Node/npm versions and can update Node via Volta.

---

## 🚀 Running the Application

```bash
# Activate your virtual environment first
python app.py
```

The development server binds to `0.0.0.0:8050`. The startup log shows `http://localhost:8050` and, when available, a LAN URL (for example `http://192.168.4.50:8050`) for other devices.

`app.py` instantiates the Dash application and exposes both `app` and `server` so the same entry point can be used by Gunicorn:

```bash
gunicorn app:server
```

The Dash factory warms caches for lookup tables (casino colours, offer keywords, hotel booking metadata) and loads the event dataset from `data/raw/casino_events.csv` at startup.

---

## 🗃️ Data pipeline

- Raw data lives in `data/raw/casino_events.csv`.
- Lookup JSON files in `data/lookups/` describe colours, offer type emojis, keyword groupings, and hotel partners.
- Casino index metadata in `data/lookups/casino_index.json` powers the legend modal that lists addresses (with directions links), hours, and other per-casino details.
- `casino_calendar.dash_app.data.loader.load_event_data()` normalises timestamps to naive UTC before the layout functions render them in Pacific Time.
- The [EventRepository](src/casino_calendar/dash_app/data/repositories.py) wrapper provides a simple interface for loading events in callbacks or tests.

If you add new columns to the CSV, update the transforms in [`src/casino_calendar/dash_app/data/transforms.py`](src/casino_calendar/dash_app/data/transforms.py) and adjust layout components that render event metadata.

---

## 🌗 Theming and styling

- SCSS sources live in `assets/styles/`. Never edit `assets/dist/style.css` directly; it is generated by the Sass build.
- Use `npm run watch:css` during development to rebuild styles on change.
- The theme toggle stores the preferred theme in a persistent Dash `dcc.Store` (`theme-store`).
- Client-side JavaScript in `assets/scripts/theme-toggle.js` applies CSS custom properties for light/dark modes.

---

## 🪵 Logging

Logging is centralised through [`casino_calendar.logging.config`](src/casino_calendar/logging/config.py).

Environment variables:

| Variable | Purpose |
| --- | --- |
| `LOG_LEVEL` | Override default log level (default: `INFO`) |
| `LOG_DIR` | Directory for log output (default: `./logs`) |
| `LOG_FILE` | Override the primary log file path (default: `LOG_DIR/app.log`) |
| `LOG_DEBUG_FILE` | Optional debug log path (set blank to disable) |
| `LOG_FILE_JSON` | Emit JSON log lines when set to `true` |
| `SUPPRESS_HTTP_LOGS` | Toggle HTTP access log capture |
| `ARCHIVE_APP_LOG_ON_STARTUP` | Archive existing log on startup (`move`, `copy`, or `false`) |
| `MAINTENANCE_LOG_LEVEL` | Console log level for maintenance scripts |
| `MAINTENANCE_LOG_FILE` | File destination for maintenance logs |

Console logs are optimized for readability (`HH:MM:SS | LEVEL | module:function:line | message`), while file logs include richer context for auditability (`YYYY-MM-DD HH:MM:SS.sss | LEVEL | pid=... tid=... | module:function:line | key=val ... | message`).

Legacy script formatters are deprecated. If you previously used `CasinoCalendarFormatter`, migrate to `casino_calendar.logging.app_logging.ConsoleFormatter`. The old name is now a compatibility shim that emits a deprecation warning.

Script output example:

Before:

```log
2025-03-01 12:00:00 | INFO     | casino_calendar.scripts.run_tests | Step: pytest
```

After:

```log
12:00:00 | INFO     | run_tests:run_step:112 | Step: pytest
```

Maintenance utilities for log cleanup live under `scripts/python/` and are documented in [docs/operations/log_management.md](docs/operations/log_management.md).

---

## 🧪 Testing and quality

```bash
# Run the Python test suite
pytest

# Run Dash integration tests (requires Chrome/Chromedriver)
pytest tests/integration

# Static analysis
black --check .
isort --check-only .
flake8 --config .flake8
npm run lint:css          # Check Sass formatting
npm run lint:css:fix      # Auto-fix Sass formatting
python scripts/python/check_environment.py  # Validate Python/Node versions
```

Continuous integration scripts (`scripts/shell/test.sh`) run the same suite locally.

---

## 🌍 Environment configuration

`src/casino_calendar/settings.py` defines helper functions for reading environment variables. Notable options:

- `DEBUG` – Enable Dash debug server features.
- `DASH_HOST` - Bind address for the Dash server (default: `0.0.0.0`).
- `DASH_PUBLIC_HOST` - Optional LAN address to advertise in startup logs (overrides auto-detect).
- `APP_TIMEZONE` – Defaults to `America/Los_Angeles`; controls how timestamps are rendered.
- `CONFIG_CACHE_BUST` – Forces configuration caches to reload JSON files.

Create a `.env` file alongside `app.py` to override these values when developing locally.

---

## 🤝 Contributing

1. Fork and clone the repository.
2. Follow the installation steps above.
3. Ensure linters and tests pass before opening a PR (`scripts/shell/test.sh`).
4. Review the documentation under [`docs/`](docs/)—especially the architecture and operations guides—before large changes.

Commit messages follow Conventional Commits with a required scope and imperative lowercase subjects. Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `merge`, `revert`. Allowed scopes: `app`, `dash`, `components`, `layout`, `styles`, `theme`, `data`, `services`, `logging`, `config`, `assets`, `scripts`, `deps`, `branch`, `tests`, `docs`, `ci`, `infra`. Run `npm run commit` (Commitizen) for a guided prompt with short type/scope descriptions enforced by `.cz-config.js`.

Issues and feature ideas are tracked in [`docs/guides/TODO.md`](docs/guides/TODO.md). Pull requests should include updates to documentation and tests where appropriate.

---

## 📚 Additional Resources

- [docs/architecture/project_structure.md](docs/architecture/project_structure.md)
- [docs/architecture/logging_system.md](docs/architecture/logging_system.md)
- [docs/guides/handoff.md](docs/guides/handoff.md)
- [docs/operations/log_management.md](docs/operations/log_management.md)
