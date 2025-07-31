# Scripts Directory

This directory contains organized utility scripts for the Casino Calendar project.

## Structure

### `maintenance/`

- **Purpose**: Log management and system maintenance utilities
- **Scripts**:
  - `cleanup_logs.py` - Log cleanup and rotation utility
  - `create_scheduled_cleanup.bat` - Windows scheduled task creator for log cleanup

### `setup/`

- **Purpose**: Initial setup and installation scripts
- **Scripts**:
  - `setup.sh` - Linux/Mac setup script for development environment

### `dev/`

- **Purpose**: Development and testing utilities
- **Scripts**:
  - `test_day_modal_fix.py` - Test script for day modal functionality
  - `test_imports.py` - Import validation script

### `test.sh`

- **Purpose**: Main test runner script
- **Usage**: Executes the full test suite

## Usage from Project Root

All scripts should be run from the project root directory:

```bash
# Log management
python scripts/maintenance/cleanup_logs.py --info

# Setup (Linux/Mac)
bash scripts/setup/setup.sh

# Development testing
python scripts/dev/test_imports.py

# Run tests
scripts/test.sh
```

## Integration with Tools

These scripts are called by tools in the `tools/` directory:

- `tools/cleanup_logs.bat` → `scripts/maintenance/cleanup_logs.py`
- `tools/setup.bat` → creates virtual environment and installs dependencies
- VSCode tasks → various scripts as needed

## Environment Requirements

- **Python 3.11+**: Required for Python scripts
- **Virtual environment**: Scripts expect `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (Linux/Mac)
- **Project context**: All scripts should be run from project root directory
