# Development Scripts

This directory contains development and testing utilities for the Casino Calendar project.

## Scripts

- `test_day_modal_fix.py` - Test script for day modal improvements
- `test_imports.py` - Verify application imports and basic functionality

## Usage

Run scripts from the project root directory:

```bash
# Test day modal functionality
python scripts/dev/test_day_modal_fix.py

# Test application imports
python scripts/dev/test_imports.py
```

## Environment Variables

These scripts respect the same environment variables as the main application:

- `LOG_LEVEL` - Set log verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `PYTHONPATH` - Project root is automatically added for imports

Example:

```bash
LOG_LEVEL=DEBUG python scripts/dev/test_imports.py
```
