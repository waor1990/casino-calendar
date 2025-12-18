# Project Organization Improvements Summary

> **📋 Note**: This document provides historical context about organization improvements made to the project. For current project structure and file organization, see [project_structure.md](project_structure.md). The original "tools/" directory referenced below has since been folded into `scripts/windows/` with lightweight launchers in the project root.

## Overview

This document summarizes the structural and organizational improvements made to the Casino Calendar project for better maintainability, clarity, and development workflow.

## Major Changes Implemented

### 1. Configuration Centralization (Previously Completed)

**Before**: Configuration files scattered in root directory
**After**: Centralized in `config/` directory

- Centralized lint/format configs: `.flake8` now lives at repo root for discoverability; `.isort.cfg`, `mypy.ini`, `.stylelintrc.json` remain under `config/`
- Updated tool configurations to reference new paths
- Removed orphaned configuration files

### 2. Script Organization

**Before**: Mixed scripts and tools in root and `scripts/` directory
**After**: Logical separation by runtime under `scripts/` with root-level launchers

#### New Structure

- **`scripts/windows/`**: User-facing batch helpers (`setup.bat`, `run_direct.bat`, `cleanup_logs.bat`, `README.md`) invoked via the root launchers.
- **`scripts/shell/`**: Unix-friendly setup and test orchestration (`setup.sh`, `test.sh`).
- **`scripts/python/`**: Maintenance utilities (log cleanup, environment checks, CSV normalisation).
- **`scripts/node/`**: Data ingestion and housekeeping scripts for CSV/Node workflows.

### 3. Root Directory Cleanup

**Before**: 27+ files in root directory
**After**: Clean root with logical organization

#### Added Convenience Launchers

- `setup.bat` - Simple launcher for `scripts\windows\setup.bat`
- `run.bat` - Simple launcher for `scripts\windows\run_direct.bat`

#### Maintained Root Files

- Core application files (`app.py`, `requirements.txt`, etc.)
- Essential configuration (`.gitignore`, `.env`, etc.)
- Documentation (`README.md`, `QUICKSTART.md`, etc.)

### 4. Archive Organization

**Before**: Old files mixed with current files
**After**: Proper archival structure

- **`archive/old_batch_files/`**: Deprecated batch scripts with documentation
- **`logs/archive/`**: Archived log files

### 5. VSCode Integration Updates

- Updated all task configurations to use new paths
- Maintained full development workflow compatibility
- Updated debug configurations
- Preserved all existing functionality

## Benefits Achieved

### For Developers

- **Clearer Structure**: Logical separation of concerns
- **Easier Navigation**: Intuitive directory organization
- **Better Documentation**: Comprehensive README files in each directory
- **Consistent Workflow**: All tools work the same way

### For Maintenance

- **Centralized Configuration**: All tool configs in one place
- **Organized Scripts**: Purpose-based script organization
- **Archive Management**: Clear separation of current vs. historical files
- **Path Consistency**: Standardized path conventions

### For New Contributors

- **Quick Start**: Simple `setup.bat` and `run.bat` commands
- **Clear Documentation**: README files explain each directory's purpose
- **Obvious Entry Points**: Root directory shows main project components
- **Development Guide**: Updated DEVELOPMENT.md with current workflow

## Directory Structure Summary

📁 Casino Calendar Root
├── 📄 app.py                    # Main application entry
├── 📄 setup.bat / run.bat       # Convenience launchers into scripts\windows\
├── 📁 scripts/                  # Organized utility scripts
│   ├── 📁 windows/              # User-facing batch helpers
│   ├── 📁 shell/                # Unix setup and test scripts
│   ├── 📁 python/               # Maintenance utilities
│   └── 📁 node/                 # Data ingestion helpers
├── 📁 src/casino_calendar/      # Application package
├── 📁 assets/                   # Static web assets (Sass + dist CSS)
├── 📁 data/                     # CSV + lookup data
├── 📁 config/                   # Tool configurations
├── 📁 docs/                     # Current documentation set
├── 📁 tests/                    # Test suite
├── 📁 legacy/                   # Archived code/docs
├── 📁 deploy/                   # Deployment configuration
└── 📁 utils/                    # Shared utilities

## Migration Path

All existing workflows continue to work:

1. **VSCode Tasks**: All tasks updated to use new paths
2. **Debug Configurations**: Continue to work without changes
3. **CI/CD**: GitHub Actions and deployment configs maintained
4. **Documentation**: All references updated to new structure

## Future Maintenance

### Adding New Scripts

- **Windows helpers**: Add batch files to `scripts/windows/` and, if needed, update the root launchers.
- **Unix helpers**: Add to `scripts/shell/`.
- **Maintenance**: Add Python utilities to `scripts/python/`.
- **Data/automation**: Add Node utilities to `scripts/node/`.

### Updating Paths

- Check `scripts/windows/` batch files and root proxies.
- Check `.vscode/tasks.json`.
- Check documentation references.
- Update README files as needed.

## Validation

All improvements have been tested:

- ✅ Tools function correctly with new paths
- ✅ VSCode tasks work properly  
- ✅ Documentation references updated
- ✅ Development workflow maintained
- ✅ Log management utilities functional

## Next Steps

1. **Optional**: Consider creating npm scripts for common tasks
2. **Optional**: Add shell script equivalents for Linux/Mac users
3. **Monitor**: Ensure new structure works well in practice
4. **Document**: Update any external documentation that references old paths

---

**Date**: Current reorganization
**Scope**: Project structure and organization
**Impact**: Improved maintainability, clearer workflow, better documentation
