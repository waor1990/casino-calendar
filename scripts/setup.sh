#!/usr/bin/env bash
# Setup script for the Codex environment.
# Installs Python and Node dependencies needed for the Casino Calendar app.

set -e

# Install Python dependencies
if [ -f requirements.txt ]; then
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
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
