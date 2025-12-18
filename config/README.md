# Configuration Files

This directory contains configuration files for development tooling used in the Casino Calendar project.

## Layout

- `ci/workflows/` – Canonical GitHub Actions workflow definitions consumed via symlinks in `.github/workflows/`.
- `formatting/` – Legacy formatting extras (`.isort.cfg` fallback for tools that cannot read `pyproject.toml`).
- `linting/` – Linting configuration (`.flake8`, `.stylelintrc.json`).
- `typing/` – Static typing configuration (`mypy.ini`).
- `pyproject.toml` (repo root) – Canonical configuration for Black, isort, Ruff, pytest, and mypy.

## Usage

These configuration files are automatically detected by their respective tools when run from the project root:

```bash
# Python formatting (uses pyproject.toml automatically)
black .
isort .

# Python linting
flake8 --config config/linting/.flake8

# Type checking
mypy --config-file config/typing/mypy.ini

# CSS linting
stylelint --config config/linting/.stylelintrc.json 'assets/**/*.scss'
```

## Pre-commit Integration

These configurations are integrated with pre-commit hooks defined in `.pre-commit-config.yaml` at the project root and mirrored in `scripts/shell/test.sh` and the GitHub Actions workflows. Keep the relative paths stable so the automation continues to resolve the files without extra flags.
