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
bash scripts/shell/setup.sh

# Run the Dash app
python app.py
```

## 📂 Key Scripts

- `setup.bat` / `scripts\windows\setup.bat` – Complete Windows setup
- `run.bat` / `scripts\windows\run_direct.bat` – Start the Dash server on Windows
- `scripts\windows\cleanup_logs.bat` – Log rotation/cleanup helper
- `scripts/shell/setup.sh` – Unix-like setup (Python + Node + Sass build)
- `scripts/shell/test.sh` – Linters plus pytest wrapper

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
- `LOG_FILE` - Optional log file path

Example:

```cmd
set LOG_LEVEL=DEBUG
set LOG_FILE=app.log
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
