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
  - `debug_errors.py` - Error debugging guide and demonstration script
  - `test_day_modal_fix.py` - Test script for day modal functionality
  - `test_imports.py` - Import validation script

### `ios/`

- **Purpose**: iOS Scriptable scripts for casino event data management
- **Scripts**:
  - `AppendCasinoEventToCSV.js` - Adds new casino events to CSV file
  - `trimOldCasinoEvents.js` - Removes old events to prevent file growth
- **Platform**: iOS Scriptable app (external to main project)
- **Integration**: Manages iCloud CSV data that syncs with main application

### iOS Scriptable Scripts (in `ios/` directory)

External scripts designed for the iOS Scriptable app to manage casino event data:

- **`AppendCasinoEventToCSV.js`** - Adds new casino events to the CSV file
  - **Platform**: iOS Scriptable app
  - **Purpose**: Appends new casino events to `data/casino_events.csv`
  - **Input**: JavaScript array of 6-item arrays (EventName, Casino, Location, Offer, StartDate, EndDate)
  - **Features**: Duplicate detection, data validation, iCloud sync
  - **Usage**: Run via iOS Shortcuts with casino event data
  - **Note**: Requires properly formatted data (no escaped characters like `\[` or `\$`)

- **`trimOldCasinoEvents.js`** - Removes old events to prevent CSV file growth
  - **Platform**: iOS Scriptable app
  - **Purpose**: Removes events older than 2 months from the CSV file
  - **Input**: None (automatically processes existing CSV)
  - **Features**: Casino-specific removal counts, robust CSV parsing, alert summary
  - **Usage**: Run periodically in Scriptable app
  - **Retention**: Keeps events from last 2 months, removes older events

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
