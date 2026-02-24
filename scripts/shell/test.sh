#!/usr/bin/env bash
# Run style checks and unit tests.

# Ensure Python uses UTF-8 for stdout/stderr to avoid encoding issues
export PYTHONIOENCODING=utf-8

set -e

# Compile Python modules (show each file being compiled for clarity)
python -m compileall -v src

# Run formatters and linter if installed
if command -v black >/dev/null 2>&1; then
    # Respect repository Black settings (via pyproject.toml) and show verbose output
    black --check --verbose .
fi
if command -v isort >/dev/null 2>&1; then
    # Use the project isort settings from pyproject.toml to align with Black and be verbose
    isort --check-only --verbose .
fi
if command -v flake8 >/dev/null 2>&1; then
    # Use the centralized flake8 config to avoid default 79 char limit and skip vendor dirs
    flake8 --config .flake8 --verbose .
fi
if command -v mypy >/dev/null 2>&1; then
    # Keep typing checks verbose for clarity during CI/runs
    mypy --config-file config/typing/mypy.ini -v
fi
if command -v bandit >/dev/null 2>&1; then
    bandit -c config/linting/bandit.yaml -f txt -r src/casino_calendar app.py wsgi.py
fi
if command -v pydocstyle >/dev/null 2>&1; then
    pydocstyle --config=config/linting/pydocstyle.ini src/casino_calendar app.py wsgi.py
fi
if command -v npm >/dev/null 2>&1; then
    npm run lint:css
fi

# Run test suite with coverage
# Print verbose test names and captured output
pytest --cov=casino_calendar -vv -s tests/
