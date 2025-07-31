# 🎰 Casino Calendar - Quick Start

## 🚀 One-Command Setup & Run

### For Windows Users

```cmd
# Setup everything (virtual env, dependencies, CSS)
setup.bat

# Run the application
run.bat

# Development mode (with CSS watching)
dev.bat
```

### For Linux/Mac Users

```bash
# Setup
scripts/setup.sh

# Run
python app.py
```

## 📂 Key Scripts

- `setup.bat` - Complete setup for Windows
- `run.bat` - Run application on Windows  
- `dev.bat` - Development mode with CSS watching
- `scripts/setup.sh` - Linux/Mac setup script
- `scripts/test.sh` - Run test suite

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

# Run tests
scripts/test.sh

# Lint code
npm run lint:css
flake8 --config config/.flake8
```
