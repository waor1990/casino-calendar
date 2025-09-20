# 🎰 Casino Event Calendar

A personal Dash application that displays casino events on a responsive calendar.
Weekly and daily views include interactive modals rendered with a CSS grid layout.

The project targets **Python 3.11** and **Node 22** (tested with **v22.9.0**).
Other versions may work but are not tested.

---

## ⚠️ CRITICAL CSS WARNING ⚠️

**🚨 NEVER modify `assets/dist/style.css` directly! It is auto-generated and will be overwritten! 🚨**

**ALL CSS changes must be made in SCSS files inside `assets/styles/`.** The `index.scss` entry compiles to `assets/dist/style.css` during the npm build step.

---

## 🚀 Features

- Weekly calendar view with color‑coded event blocks
- Modal windows for detailed event and day information
- CSS grid layout for weekly view
- Responsive design for desktop, tablet and mobile
- Times stored in UTC and displayed in Pacific Time (PDT)
- Toggle to show ongoing events that span the week
- Auto-categorizes offers into Giveaway, Free-Play, Point-Based, Hospitality-Rewards and Special-Events
- **Hotel booking links** that appear when a casino is selected from the legend
- SCSS styles compiled with Sass
- **Comprehensive logging system** for debugging and monitoring

---

## 📁 Project Layout

> For detailed project structure documentation, see [docs/architecture/project_structure.md](docs/architecture/project_structure.md).

```text
app.py                   # Dash entry point exposing Dash server
wsgi.py                  # Optional WSGI shim exporting application
deploy/                  # Deployment descriptors
  Procfile
  render.yaml
  gunicorn.conf.py
src/
  casino_calendar/       # Primary Python package
    settings.py          # Environment and path helpers
    dash_app/            # Dash application modules
      app.py             # create_dash_app factory
      callbacks/         # Callback groups (events, filters, theme, navigation)
      data/              # Loader, repositories, transforms
      layout/            # Layout factory and component helpers
      services/          # Dash-specific services (layout state, etc.)
      visualization/     # Plotly figure builders
    logging/             # Logging configuration and rotation utilities
    services/            # General-purpose services (colors, config cache)
assets/
  dist/                 # Compiled CSS artifacts (generated)
  scripts/theme-toggle.js
  styles/index.scss     # Sass entry point
  styles/partials/      # Reusable Sass modules
config/
  formatting/           # Formatting tool configuration
    pyproject.toml
    .isort.cfg
  linting/              # Linting configuration
    .flake8
    .stylelintrc.json
  typing/               # Static typing configuration
    mypy.ini
data/
  raw/casino_events.csv # Primary dataset
  lookups/              # JSON lookup tables (colors, keywords, etc.)
  cache/                # Runtime cache artifacts
docs/
  legacy/               # Historical documentation and archived notes
scripts/
  python/               # Python maintenance utilities
  shell/                # Bash helpers (setup, test)
  node/                 # Scriptable/Node automation helpers
  windows/              # Windows batch launchers
logs/                    # Application log files
tests/
  unit/
  integration/
  e2e/
requirements.txt         # Python dependencies
package.json             # NPM scripts for Sass/CSS pipeline
```

## 🧪 Try It Locally

### Windows (Recommended)

```cmd
# Quick setup - runs everything needed
scripts\windows\setup.bat

# Run the application
scripts\windows
un_direct.bat

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    # calls scripts\windows
un_direct.bat
```

### Linux/Mac

```bash
python3 -m venv .venv
source .venv/bin/activate
scripts/shell/setup.sh           # install Python and Node dependencies
npm install
npm run build:css  # compiles assets/styles/index.scss to assets/dist/style.css (edit SCSS only)
npm run lint:css
pip install -r requirements.txt
pre-commit install
pre-commit run --all-files
python -m compileall src
scripts/shell/test.sh             # run linters and tests
python app.py
```

On Windows you can run everything from one command by executing `scripts\windowsun_direct.bat`
or the convenience launcher `run.bat` in a Command Prompt or the VS Code terminal:

```cmd
scripts\windowsun_direct.bat
# Or use the convenience launcher:
run.bat
```


## 📊 Logging System

The application includes a comprehensive logging system for debugging and monitoring:

### Quick Start

```bash
# Run with default logging (INFO level, console output)
python app.py

For detailed documentation, see [`docs/architecture/logging_system.md`](docs/architecture/logging_system.md).
LOG_LEVEL=DEBUG python app.py

# Enable file logging
LOG_FILE=logs/app.log python app.py

# Production logging
LOG_LEVEL=WARNING LOG_FILE=logs/production.log gunicorn app:server
```

### Features

- **Configurable log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **File and console output** with automatic log rotation
- **Color-coded console output** for better readability
- **Performance timing** for key operations
- **Structured error logging** with stack traces
- **Client-side JavaScript logging** in browser console

### Configuration

Set environment variables to control logging:

- `LOG_LEVEL`: Minimum log level (default: INFO)
- `LOG_FILE`: Optional file output path

For detailed documentation, see [`docs/logging_system.md`](docs/logging_system.md).

## 🌍 Deployment

Hosted at [https://casino-calendar.onrender.com](https://casino-calendar.onrender.com)

`Procfile`:

```txt
web: gunicorn app:server
```

## 🤝 Contributing

Please follow the development guidelines in `AGENTS.md` when proposing
changes. Run the formatters and linters before committing and see
`GIT-CHEATSHEET.md` for handy Git commands.

### Git Helper: CSV Update Alias

For quick commits when only `data/casino_events.csv` changes, add a repo‑local alias:

- Create alias: `git config --local alias.csvupdate '!git add data/casino_events.csv && git commit -m "chore(data): update casino_events.csv"'`
- Use it: `git csvupdate`
- Optional (with push): `git config --local alias.csvupdate '!git add data/casino_events.csv && git commit -m "chore(data): update casino_events.csv" && git push'`

See `GIT-CHEATSHEET.md` for editing/removing the alias and more details.
VSCode users can take advantage of the included `.editorconfig` and
`.vscode` files so formatting and linting run automatically on save.

### Branch strategy

Use prefix-based branches when contributing:

- `feature/` for new functionality
- `fix/` for bug fixes
- `refactor/` for internal improvements
- `test/` for test additions
- `doc/` for documentation updates

## 🧼 License

Released under [The Unlicense](https://unlicense.org).
