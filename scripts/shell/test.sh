#!/usr/bin/env bash
# Run style checks and unit tests.

# Ensure Python uses UTF-8 for stdout/stderr to avoid encoding issues
export PYTHONIOENCODING=utf-8

set -e

# Compile Python modules
python -m compileall src

# Run formatters and linter if installed
if command -v black >/dev/null 2>&1; then
    # Respect repository Black settings (via pyproject.toml)
    black --check .
fi
if command -v isort >/dev/null 2>&1; then
    # Use the project isort settings to align with Black
    isort --check-only --settings-path config/formatting/.isort.cfg .
fi
if command -v flake8 >/dev/null 2>&1; then
    # Use the centralized flake8 config to avoid default 79 char limit
    flake8 --config config/linting/.flake8 .
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
# Print verbose test names and captured output
pytest --cov=casino_calendar -vv -s tests/
