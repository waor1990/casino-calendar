#!/usr/bin/env bash
# Setup script for the Codex environment.
# Installs Python and Node dependencies needed for the Casino Calendar app.

set -e

# Creat and activate a virtual environment if not already present
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate the venv (will work within Codex)
source .venv/bin/activate

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
    pre-commit install
fi
