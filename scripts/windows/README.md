# Windows Scripts

Batch helpers for setting up, running, and maintaining the Casino Calendar app. Root launchers (`setup.bat`, `run.bat`) proxy to the scripts in this folder.

## Quick Start

1. `setup.bat` (or `scripts\windows\setup.bat`) to create/validate `.venv`, install Python deps, validate `package.json`, clean npm staging dirs, run `npm install`, and install pre-commit hooks.
2. **Option A:** `run.bat` (or `scripts\windows\run_direct.bat`) to build CSS and start only the Dash server on <http://localhost:8050>. Assumes the REST API is already running.
3. **Option B:** `scripts\windows\start_all.bat` to start both the REST API and Dash app in separate windows.

## Script Details

- `setup.bat` – Creates the virtual environment if missing, checks for stale venvs, dry-runs pip to highlight dependency drift, installs Python requirements, validates `package.json`, cleans npm staging directories, runs `npm install`, and installs pre-commit hooks when available.
- `run_direct.bat` – Ensures `.venv` exists, sets UTF-8 console encoding, builds `assets/dist/style.css` via `npm run build:css` if npm is available, and launches the app with the venv Python. Requires REST API to be running separately.
- `start_all.bat` – Starts both the REST API (port 5001) and Dash application (port 8050) in separate windows. Includes automatic CSS build and health check on startup.
- `start_api.bat` – Starts only the REST API server on port 5001.
- `start_dash.bat` – Starts only the Dash application on port 8050. Requires REST API to be running separately.
- `cleanup_logs.bat` – Rotate/prune log files; supports `--info`, `--dry-run`, and `--archive`.
- `create_scheduled_cleanup.bat` – Optional scheduled task creator for periodic log cleanup.

## Startup Options

### Development with Auto-Start (Recommended)

```cmd
scripts\windows\start_all.bat
```

This opens two new windows:

- One for the REST API (handles event data)
- One for the Dash application (web interface)

### Manual Service Management

```cmd
REM Terminal 1: Start REST API
scripts\windows\start_api.bat

REM Terminal 2: Start Dash App (in another window)
scripts\windows\start_dash.bat
```

### API Health Check

The Dash application now includes automatic health checks:

- Waits up to 10 seconds for the API to become available
- Retries with exponential backoff
- Provides clear error messages if API is unavailable
- Will not start without a healthy API connection

## VSCode Integration

The F5 debug profile and "Run Casino Calendar App" task call `scripts\windows\run_direct.bat`. Log cleanup tasks call the Python maintenance script directly. Keep the script paths stable if you adjust tasks or launch configurations.

For development, consider adding a task to run `start_all.bat` instead for a complete startup experience.
