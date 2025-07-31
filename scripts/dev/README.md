# Development Scripts

This directory contains development and testing utilities for the Casino Calendar project.

## Scripts

- `demo_logging.py` - Demonstrates the logging system capabilities
- `test_logging.py` - Comprehensive logging system tests
- `test_logging_complete.py` - Full application logging verification

## Usage

Run scripts from the project root directory:

```bash
# Demonstrate logging system
python scripts/dev/demo_logging.py

# Test logging functionality
python scripts/dev/test_logging.py

# Complete logging verification
python scripts/dev/test_logging_complete.py
```

## Environment Variables

These scripts respect the same logging environment variables as the main application:

- `LOG_LEVEL` - Set log verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FILE` - Optional file output path

Example:

```bash
LOG_LEVEL=DEBUG LOG_FILE=dev.log python scripts/dev/demo_logging.py
```
