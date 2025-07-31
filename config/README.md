# Configuration Files

This directory contains configuration files for various development tools and linters used in the Casino Calendar project.

## Files

- `.flake8` - Python linting configuration for flake8
- `.isort.cfg` - Import sorting configuration for isort  
- `mypy.ini` - Type checking configuration for mypy
- `.stylelintrc.json` - CSS/SCSS linting configuration for stylelint

## Usage

These configuration files are automatically detected by their respective tools when run from the project root:

```bash
# Python linting
flake8 --config config/.flake8

# Import sorting  
isort --settings-path config/.isort.cfg

# Type checking
mypy --config-file config/mypy.ini

# CSS linting
stylelint --config config/.stylelintrc.json 'assets/**/*.scss'
```

## Pre-commit Integration

These configurations are integrated with pre-commit hooks defined in `.pre-commit-config.yaml` at the project root.

## NPM Scripts

The stylelint configuration is also used by the npm script:

```bash
npm run lint:css
```
