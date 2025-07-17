#!/usr/bin/env bash
# Run style checks and unit tests.

set -e

# Compile Python modules
python -m py_compile app.py app_components/*.py

# Run formatters and linter if installed
if command -v black >/dev/null 2>&1; then
    black --check .
fi
if command -v isort >/dev/null 2>&1; then
    isort --check-only .
fi
if command -v flake8 >/dev/null 2>&1; then
    flake8 .
fi
if command -v mypy >/dev/null 2>&1; then
    mypy .
fi
if command -v bandit >/dev/null 2>&1; then
    bandit -r .
fi
if command -v pydocstyle >/dev/null 2>&1; then
    pydocstyle .
fi
if command -v npm >/dev/null 2>&1; then
    npm run lint:css
fi

# Run test suite with coverage
pytest --cov=app_components tests/ -q
