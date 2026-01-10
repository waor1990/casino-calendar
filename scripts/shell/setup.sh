#!/usr/bin/env bash
# Setup script for the Codex environment.
# Installs Python and Node dependencies needed for the Casino Calendar app.

set -e

# Create and activate a virtual environment if not already present
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate the venv (prefer Unix path, fallback to Windows path)
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
else
    echo "[ERROR] Could not find venv activation script in .venv."
    exit 1
fi

# Now install Python dependencies
if [ -f requirements.txt ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Install Node dependencies if npm is available
if command -v npm >/dev/null 2>&1; then
    npm install
    npm run build:css
fi

# Install pre-commit hooks if available
if command -v pre-commit >/dev/null 2>&1; then
    hooks_path="$(git config --get core.hooksPath || true)"
    if [ -n "$hooks_path" ]; then
        echo "[WARN] Skipping pre-commit install because core.hooksPath is set to '$hooks_path'."
        echo "       To enable hooks, run: git config --unset-all core.hooksPath"
    else
        pre-commit install
    fi
fi
