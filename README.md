# 🎰 Casino Event Calendar

A personal Dash application that displays casino events on a responsive calendar.
Weekly and daily views include interactive modals rendered with a CSS grid layout.

The project targets **Python 3.11** and **Node 18**.  Other versions may work
but are not tested.

---

## ⚠️ CRITICAL CSS WARNING ⚠️

**🚨 NEVER modify `assets/style.css` directly! It is auto-generated and will be overwritten! 🚨**

**ALL CSS changes must be made in SCSS files in `assets/styles/` directory.** The `style.css` file is automatically compiled from SCSS when the app runs.

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

> For detailed project structure documentation, see [docs/project_structure.md](docs/project_structure.md).

```text
app.py                   # Dash entry point
app_components/          # Core logic modules
  callbacks/             # Dash callback handlers
  utils/                 # Shared helper functions
assets/                  # Static assets auto-loaded by Dash
archive/                 # Archived files and directories
  old_batch_files/       # Deprecated batch scripts
config/                  # Tool configuration files
  .flake8              # Python linting config
  .isort.cfg           # Import sorting config
  mypy.ini             # Type checking config
  .stylelintrc.json    # CSS linting config
data/                    # CSV data files
  casino_events.csv
  docs/                    # Project documentation
    archived/            # Completed/historical docs
    handoff.md
    TODO.md              # Next steps and project improvements
    logging_system.md
logs/                    # Application log files
  archive/             # Archived log files
scripts/                 # Utility scripts
  dev/                 # Development tools
  maintenance/         # Log cleanup and maintenance
  setup/               # Setup and installation scripts
tests/                   # Test suite
tools/                   # User-facing utility scripts
  setup.bat            # Environment setup
  run_direct.bat       # Application launcher
  cleanup_logs.bat     # Log management
utils/                   # Shared utilities
requirements.txt         # Python dependencies
package.json             # NPM scripts for Sass
Procfile                 # Heroku deployment configuration  
render.yaml              # Render.com deployment configuration
```

## 🧪 Try It Locally

### Windows (Recommended)

```cmd
# Quick setup - runs everything needed
tools\setup.bat

# Run the application  
tools\run_direct.bat

# Or use convenience launchers
setup.bat  # calls tools\setup.bat
run.bat    # calls tools\run_direct.bat
```

### Linux/Mac

```bash
python3 -m venv .venv
source .venv/bin/activate
scripts/setup/setup.sh           # install Python and Node dependencies
npm install
npm run build:css  # compiles assets/style.scss to assets/style.css (DO NOT EDIT style.css directly!)
npm run lint:css
pip install -r requirements.txt
pre-commit install
pre-commit run --all-files
python -m py_compile app.py app_components/*.py
scripts/test.sh                  # run linters and tests
python app.py
```

On Windows you can run everything from one command by executing `tools\run_direct.bat`
or the convenience launcher `run.bat` in a Command Prompt or the VSCode terminal:

```cmd
tools\run_direct.bat
# Or use the convenience launcher:
run.bat
```

## 📊 Logging System

The application includes a comprehensive logging system for debugging and monitoring:

### Quick Start

```bash
# Run with default logging (INFO level, console output)
python app.py

# Enable debug logging
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
