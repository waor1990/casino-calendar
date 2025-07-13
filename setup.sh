#!/usr/bin/env bash
set -e

# Create and activate a virtual environment if not already present
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# Install Python dependencies
if [ -f requirements.txt ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Install Node dependencies & build CSS
if command -v npm >/dev/null 2>&1; then
    npm install
    npm run build:css
fi

# Install pre-commit hooks 
if command -v pre-commit >/dev/null 2>&1; then
    pre-commit install
fi
