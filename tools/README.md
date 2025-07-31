# Tools Directory

This directory contains utility scripts and batch files for managing the Casino Calendar application.

## Quick Start Scripts

These scripts provide convenient access to main functionality:

### `setup.bat`

- **Purpose**: Initial project setup and dependency installation
- **Usage**: Double-click or run `tools\setup.bat`
- **What it does**:
  - Creates Python virtual environment
  - Installs Python dependencies from requirements.txt
  - Installs Node.js dependencies (if npm available)
  - Installs pre-commit hooks
  - Prepares environment for development

### `run_direct.bat`

- **Purpose**: Run the Casino Calendar application
- **Usage**: Double-click or run `tools\run_direct.bat`
- **What it does**:
  - Activates virtual environment
  - Builds CSS from SCSS (if npm available)
  - Starts the Dash application on <http://localhost:8050>
  - Provides detailed status messages

### `cleanup_logs.bat`

- **Purpose**: Log file management and cleanup
- **Usage**:
  - `tools\cleanup_logs.bat` - Clean logs older than 30 days
  - `tools\cleanup_logs.bat --info` - Show log directory information
  - `tools\cleanup_logs.bat --dry-run` - Preview what would be deleted
  - `tools\cleanup_logs.bat --archive` - Archive current log file

## Root Directory Convenience Scripts

The project root contains simple launcher scripts that call the tools:

- `setup.bat` → `tools\setup.bat`
- `run.bat` → `tools\run_direct.bat`

This design keeps the root directory clean while maintaining easy access to common operations.

## Integration with Development Environment

### VSCode Tasks

All tools are integrated with VSCode tasks accessible via `Ctrl+Shift+P` → "Tasks: Run Task":

- **Run Casino Calendar App**: Uses `tools\run_direct.bat`
- **Log Cleanup - Info**: Uses Python script directly  
- **Log Cleanup - Execute**: Uses Python script directly

### Debug Configurations

VSCode debug configurations (F5) also use these tools for consistent environment setup.

## Organization

Tools are organized for clarity:

- **Root-level batch files**: Primary user interface, kept minimal
- **tools/ directory**: Implementation scripts with full functionality
- **scripts/maintenance/**: Python utilities for log management
- **scripts/setup/**: Setup and installation scripts
- **scripts/dev/**: Development and testing utilities

## Dependencies

- **Python 3.11+**: Required for application and scripts
- **Node.js/npm**: Optional, for CSS building
- **Virtual environment**: Created automatically by setup

## Error Handling

All batch files include:

- Environment validation
- Clear error messages
- Graceful fallbacks where possible
- Detailed status reporting

## Maintenance

These tools are designed to be self-contained and require minimal maintenance. If paths change, update:

1. Root launcher scripts (setup.bat, run.bat)
2. VSCode tasks.json
3. Documentation references
4. Internal script paths
