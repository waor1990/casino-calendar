# Casino Calendar - Development Setup Guide

## Environment Configuration

This workspace is configured for developing the Casino Calendar Dash application.

### Quick Start

1. **Open in VSCode**: The workspace will use the virtual environment automatically
2. **Run Application**: Use one of these methods:
   - Press `F5` and select "Casino Calendar - Debug"
   - Use `Ctrl+Shift+P` → "Tasks: Run Task" → "Run Casino Calendar App"
   - Use the Run and Debug panel (`Ctrl+Shift+D`)

### Development Features Configured

- ✅ Python virtual environment (`.venv/`)
- ✅ Debug configurations for development and production
- ✅ Auto-formatting with Black
- ✅ Import sorting with isort
- ✅ Linting with flake8
- ✅ Testing with pytest
- ✅ Log management and cleanup tasks
- ✅ Working VSCode tasks that bypass auto-activation issues

### Available Debug Configurations

1. **Casino Calendar - Debug**: Runs with debug logging enabled
2. **Casino Calendar - Production**: Runs with production settings
3. **Run Tests**: Executes pytest test suite
4. **Log Cleanup Script**: Runs log management utilities

### Available Tasks (Ctrl+Shift+P → Tasks: Run Task)

1. **Run Casino Calendar App**: Starts the application (DEFAULT - F5 equivalent)
2. **Test Python Environment**: Validates all dependencies and imports
3. **Run Tests**: Executes pytest test suite
4. **Install Dependencies**: Installs/updates requirements.txt
5. **Log Cleanup - Info**: Shows log cleanup information
6. **Log Cleanup - Execute**: Performs log cleanup

### Browser Access

- **Development URL**: <http://localhost:8050>
- **Debug Browser**: Use "Launch Dash in Edge" configuration for debugging

### Troubleshooting

If the application doesn't start:

1. Verify virtual environment exists: Check for `.venv/Scripts/python.exe`
2. Run "Install Dependencies" task to ensure all packages are installed
3. Run "Test Python Environment" to verify setup
4. Check logs in `logs/` directory for detailed error information

### Environment Variables

The following variables are set automatically:

- `PYTHONPATH`: Project root directory
- `LOG_LEVEL`: DEBUG (development) or INFO (production)
- `PROJECT_ROOT`: Workspace folder path

### Technical Notes

- Tasks use direct command execution to avoid auto-activation conflicts
- All tasks create new terminal panels for clear output
- Background tasks (like running the app) continue until stopped
- The application runs on port 8050 by default
