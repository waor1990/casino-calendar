# Configuration Files

This directory contains configuration files for development tooling used in the Casino Calendar project.

## Layout

- `ci/workflows/` – Canonical GitHub Actions workflow definitions consumed via symlinks in `.github/workflows/`.
- `formatting/` – Code formatting configuration (`pyproject.toml`, `.isort.cfg`).
- `linting/` – Linting configuration (`.flake8`, `.stylelintrc.json`).
- `typing/` – Static typing configuration (`mypy.ini`).

## Usage

These configuration files are automatically detected by their respective tools when run from the project root:

```bash
# Python linting
flake8 --config config/linting/.flake8

# Import sorting
isort --settings-path config/formatting/.isort.cfg

# Type checking (mypy_path points at ../../src relative to this file)
mypy --config-file config/typing/mypy.ini

# CSS linting
stylelint --config config/linting/.stylelintrc.json 'assets/**/*.scss'
```

## Pre-commit Integration

These configurations are integrated with pre-commit hooks defined in `.pre-commit-config.yaml` at the project root and mirrored in `scripts/shell/test.sh`.
