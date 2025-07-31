# Archived Batch Files

This directory contains batch files that were removed from the main project directory because they are no longer needed or were causing conflicts with the current VSCode development setup.

## Files Archived

### `run_app.bat`
- **Purpose**: Simple application runner
- **Reason for archival**: Superseded by `run_direct.bat` which has better error handling and status messages
- **Replacement**: Use VSCode task "Run Casino Calendar App" or `run_direct.bat`

### `run.bat`
- **Purpose**: Application runner with virtual environment activation
- **Reason for archival**: Superseded by `run_direct.bat`
- **Replacement**: Use VSCode task "Run Casino Calendar App" or `run_direct.bat`

### `dev.bat`
- **Purpose**: Development mode runner with CSS watching
- **Reason for archival**: CSS watching functionality not integrated into current workflow
- **Replacement**: Use VSCode task "Run Casino Calendar App" for development

### `dev_test.bat`
- **Purpose**: Development environment testing script
- **Reason for archival**: Superseded by VSCode task "Test Python Environment"
- **Replacement**: Use VSCode task "Test Python Environment"

### `auto_activate.bat`
- **Purpose**: Automatic virtual environment activation for VSCode terminals
- **Reason for archival**: **CAUSED TASK EXECUTION CONFLICTS** - Was interfering with VSCode task execution, causing tasks to hang
- **Replacement**: VSCode settings now use "Command Prompt" as default terminal profile

### `setup_terminal.bat`
- **Purpose**: VSCode terminal environment setup
- **Reason for archival**: No longer needed with current VSCode configuration
- **Replacement**: Current VSCode settings handle terminal setup automatically

## Current Active Batch Files

The following batch files remain active in the main directory:

- ✅ **`run_direct.bat`** - Primary application runner used by VSCode tasks
- ✅ **`setup.bat`** - Initial project setup and virtual environment creation
- ✅ **`cleanup_logs.bat`** - Log management utility used by VSCode tasks

## Migration Notes

If you need to restore any of these files for compatibility or specific use cases, they can be copied back from this archive. However, be aware that:

1. `auto_activate.bat` will likely cause VSCode task execution issues if restored
2. The other runners are functionally replaced by the current VSCode task system
3. All functionality is available through VSCode tasks: `Ctrl+Shift+P` → "Tasks: Run Task"

## Date Archived
July 30, 2025

## Related Changes
- VSCode tasks.json cleaned up to use direct command execution
- Terminal default profile changed from "Casino Calendar Environment" to "Command Prompt"
- DEVELOPMENT.md updated with current workflow instructions
