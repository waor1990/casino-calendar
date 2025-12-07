# Windows Scripts

Batch helpers for setting up, running, and maintaining the Casino Calendar app. Root launchers (`setup.bat`, `run.bat`) proxy to the scripts in this folder.

## Quick Start

1. `setup.bat` (or `scripts\windows\setup.bat`) to create/validate `.venv`, install Python deps, validate `package.json`, clean npm staging dirs, run `npm install`, and install pre-commit hooks.
2. `run.bat` (or `scripts\windows\run_direct.bat`) to build CSS via npm and start the Dash server on <http://localhost:8050>.

## Script Details

- `setup.bat` – Creates the virtual environment if missing, checks for stale venvs, dry-runs pip to highlight dependency drift, installs Python requirements, validates `package.json`, cleans npm staging directories, runs `npm install`, and installs pre-commit hooks when available.
- `run_direct.bat` – Ensures `.venv` exists, sets UTF-8 console encoding, builds `assets/dist/style.css` via `npm run build:css` if npm is available, and launches the app with the venv Python.
- `cleanup_logs.bat` – Rotate/prune log files; supports `--info`, `--dry-run`, and `--archive`.
- `create_scheduled_cleanup.bat` – Optional scheduled task creator for periodic log cleanup.

## VSCode Integration

The F5 debug profile and "Run Casino Calendar App" task call `scripts\windows\run_direct.bat`. Log cleanup tasks call the Python maintenance script directly. Keep the script paths stable if you adjust tasks or launch configurations.
