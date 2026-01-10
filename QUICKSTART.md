# 🎰 Casino Calendar - Quick Start

## 🚀 One-Command Setup & Run

### Windows

```cmd
# Bootstrap dependencies and the virtual environment
setup.bat

# Launch the Dash app (proxies to scripts\windows\run_direct.bat)
run.bat
```

The full-featured scripts live under `scripts\windows\` if you want to call them directly (`setup.bat`, `run_direct.bat`, `cleanup_logs.bat`).

### Linux / macOS

```bash
# Bootstrap dependencies, build CSS, and install pre-commit hooks
source scripts/shell/setup.sh

# Run the Dash app
python app.py
```

The development server binds to `0.0.0.0:8050`. The startup log shows `http://localhost:8050` and, when available, a LAN URL (for example `http://192.168.4.50:8050`) for other devices.

## 📂 Key Scripts

- `setup.bat` / `scripts\windows\setup.bat` – Complete Windows setup
- `run.bat` / `scripts\windows\run_direct.bat` – Start the Dash server on Windows
- `scripts\windows\cleanup_logs.bat` – Log rotation/cleanup helper
- `scripts/shell/setup.sh` – Unix-like setup (Python + Node + Sass build). If `core.hooksPath` is set, pre-commit hooks are skipped; run `git config --unset-all core.hooksPath` to enable hooks.
- `scripts/shell/test.sh` – Linters plus pytest wrapper
- `test.bat` / `scripts\windows\test.bat` - Windows test runner (compile checks, linters, CSS lint, pytest); logs timestamped output to `logs\casino_calendar_batch_test_windows.log` (override with `WIN_TEST_BAT_LOG_FILE`), writes Bandit/Pydocstyle reports to `logs\bandit_report.txt` and `logs\pydocstyle_report.txt` (Bandit/Pydocstyle focus on `src\casino_calendar` plus `app.py`/`wsgi.py` via `config\linting\bandit.yaml` and `config\linting\pydocstyle.ini`)
- `scripts/python/check_environment.py` - Validate Python/Node/npm versions (supports `--auto-fix` with Volta)
- `scripts/python/verify_requirements.py` - Compare installed packages to `requirements.txt`

## 🔧 Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
npm install

# Build CSS
npm run build:css

# Install pre-commit hooks
pre-commit install

# Run application
python app.py
```

## 📊 Environment Variables

- `LOG_LEVEL` - Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_DIR` - Directory for log output (default: `./logs`)
- `LOG_FILE` - Optional log file path override (default: `LOG_DIR/app.log`)
- `LOG_DEBUG_FILE` - Optional debug log override (set blank to disable)
- `LOG_FILE_JSON` - Set `true` to emit JSON log lines to files
- `*_BAT_LOG_FILE` - Batch script log destinations (see `.env.example` for defaults)
- Batch script logs mirror console output and apply the standard `timestamp | level | source | message` format
- `DASH_HOST` - Bind address for the Dash server (default: `0.0.0.0`)
- `DASH_PUBLIC_HOST` - Optional LAN address to advertise in startup logs (overrides auto-detect)

Example:

```cmd
set LOG_LEVEL=DEBUG
set LOG_FILE=app.log
set LOG_FILE_JSON=true
run.bat
```

## 🧪 Development

```bash
# Watch CSS changes
npm run watch:css

# Run tests and linters
bash scripts/shell/test.sh
pytest
black .
isort .
flake8 --config .flake8
npm run lint:css
```
