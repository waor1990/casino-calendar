# Casino Calendar - Development Setup Guide

## Environment Configuration

This workspace is configured for developing the Casino Calendar Dash application.

### Quick Start

1. **Open in VSCode**: The workspace should automatically activate the virtual environment
2. **Run Application**: Use one of these methods:
   - Press `F5` and select "Casino Calendar - Debug"
   - Use `Ctrl+Shift+P` → "Tasks: Run Task" → "Run Casino Calendar - Debug Mode"
   - Use the Run and Debug panel (`Ctrl+Shift+D`)

### Development Features Configured

- ✅ Python virtual environment (`.venv/`)
- ✅ Debug configurations for development and production
- ✅ Auto-formatting with Black
- ✅ Import sorting with isort
- ✅ Linting with flake8
- ✅ Testing with pytest
- ✅ Log management and cleanup tasks

### Available Debug Configurations

1. **Casino Calendar - Debug**: Runs with debug logging enabled
2. **Casino Calendar - Production**: Runs with production settings
3. **Run Tests**: Executes pytest test suite
4. **Log Cleanup Script**: Runs log management utilities

### Available Tasks (Ctrl+Shift+P → Tasks: Run Task)

1. **Setup Terminal Environment**: Initializes the development environment
2. **Run Casino Calendar**: Starts the application (background process)
3. **Run Casino Calendar - Debug Mode**: Starts with debug logging
4. **Test Casino Calendar Imports**: Validates all dependencies
5. **Run Test Script**: Executes pytest
6. **Log Cleanup tasks**: Various log management operations
7. **Install Dependencies**: Installs requirements.txt

### Browser Access

- **Development URL**: <http://localhost:8050>
- **Debug Browser**: Use "Launch Dash in Edge" configuration for debugging

### Troubleshooting

If the application doesn't start:

1. Check that the virtual environment is activated
2. Verify dependencies are installed: Run "Install Dependencies" task
3. Check logs in `logs/` directory
4. Run "Test Casino Calendar Imports" to verify setup

### Environment Variables

The following variables are set automatically:

- `PYTHONPATH`: Project root directory
- `LOG_LEVEL`: DEBUG (development) or INFO (production)
- `PROJECT_ROOT`: Workspace folder path
