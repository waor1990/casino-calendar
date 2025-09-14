# Project Structure Documentation

This document provides a comprehensive overview of the Casino Calendar project structure, including the organization philosophy and detailed explanations of all directories and files.

## Organization Philosophy

The project follows a clear separation of concerns:

- **Root directory**: Contains only essential files for immediate project understanding and quick access
- **Functional directories**: Grouped by purpose (`app_components/`, `tests/`, `scripts/`, etc.)
- **User-facing tools**: Centralized in `tools/` with convenience launchers in root
- **Configuration**: Centralized in `config/` directory
- **Documentation**: Organized in `docs/` directory

## Root Directory Files

### Core Application Files

- `app.py` - Main Dash application entry point
- `requirements.txt` - Python dependencies
- `Procfile` - Heroku deployment configuration
- `render.yaml` - Render.com deployment configuration

### Quick Access Launchers

These provide convenient access to tools without needing to navigate to subdirectories:

- `setup.bat` - Quick setup launcher (calls `tools\setup.bat`)
- `run.bat` - Quick run launcher (calls `tools\run_direct.bat`)
- `cleanup.bat` - Quick log cleanup launcher (calls `tools\cleanup_logs.bat`)

### Frontend Build Tools

- `package.json` - Node.js dependencies for SCSS compilation and CSS linting
- `package-lock.json` - Locked dependency versions
- `node_modules/` - Node.js dependencies (generated)

### Configuration Files

- `.env` - Environment variables (local, not in version control)
- `.env.example` - Environment variables template
- `.gitignore` - Git ignore patterns
- `.pre-commit-config.yaml` - Pre-commit hooks configuration

### Documentation

- `README.md` - Main project documentation and quick start guide
- `QUICKSTART.md` - Simplified quick start instructions
- `DEVELOPMENT.md` - Development setup and guidelines
- `LICENSE` - Project license
- `AGENTS.md` - AI agents and automation documentation

## Project Directories

### Core Application (`app_components/`)

Contains the main Dash application logic:

- `__init__.py` - Package initialization
- `data.py` - Data loading and processing
- `layout.py` - Dash layout components
- `logging_config.py` - Logging configuration
- `plotting.py` - Chart and visualization generation
- `utils.py` - Shared utility functions
- `week_grid_layout.py` - Weekly calendar grid layout
- `callbacks/` - Dash callback handlers
  - `events.py` - Event-related callbacks
  - `filters.py` - Filtering callbacks
  - `theme.py` - Theme switching callbacks

### Static Assets (`assets/`)

Auto-loaded by Dash for frontend resources:

- `base.css` - Base CSS styles
- `style.css` - **AUTO-GENERATED** compiled stylesheet (**DO NOT EDIT DIRECTLY**)
- `style.scss` - Main SCSS source file (edit this instead of style.css)
- `theme-toggle.js` - Theme switching JavaScript
- `styles/` - SCSS partials and modules (all CSS changes go here)

### Configuration (`config/`)

Centralized tool configuration files:

- `mypy.ini` - Type checking configuration
- `README.md` - Configuration documentation

### Data (`data/`)

Project data files and resources:

- `casino_events.csv` - Main event data
- `casino_colors.json` - Casino color schemes
- `default_colors.json` - Default color palette
- `hotel_book_sites.json` - Hotel booking site links
- `offer_keywords.json` - Offer categorization keywords
- `offer_type_emojis.json` - Emoji mappings for offer types

### Documentation (`docs/`)

Comprehensive project documentation:

- `archived/organization_summary.md` - Historical organization improvements
- `logging_system.md` - Logging system documentation
- `handoff.md` - Project handoff documentation
- `TODO.md` - Next steps and project improvements
- `archived/` - Completed or historical documentation

### Scripts (`scripts/`)

Organized by purpose:

- `maintenance/` - System maintenance utilities
  - `cleanup_logs.py` - Log cleanup and rotation
- `setup/` - Installation and setup scripts
  - `setup.sh` - Linux/Mac setup script
- `dev/` - Development and testing utilities

### Tests (`tests/`)

Comprehensive test suite:

- `conftest.py` - Pytest configuration
- `test_*.py` - Various test modules for different components
- `__pycache__/` - Python bytecode cache

### Tools (`tools/`)

User-facing utility scripts:

- `setup.bat` - Environment setup and dependency installation
- `run_direct.bat` - Application launcher with environment activation
- `cleanup_logs.bat` - Log management utility
- `README.md` - Tools documentation

### Utilities (`utils/`)

Shared utility modules:

- `colors.py` - Color handling utilities
- `data_parsing.py` - Data parsing functions
- `log_rotation.py` - Log rotation utilities

### Other Directories

- `archive/` - Archived/deprecated files with historical value
- `logs/` - Application log files (runtime generated)

## Generated/Cache Directories

These are created automatically and should not be manually modified:

- `.git/` - Git repository data
- `.github/` - GitHub Actions and templates
- `.pytest_cache/` - Pytest cache
- `.venv/` - Python virtual environment
- `.vscode/` - VS Code workspace settings
- `node_modules/` - Node.js dependencies

## Development Workflow

### Quick Start

```cmd
setup.bat    # Initial setup
run.bat      # Run the application
cleanup.bat  # Clean up logs
```

### Full Development Setup

```cmd
tools\setup.bat      # Complete environment setup
tools\run_direct.bat # Run with full debugging
tools\cleanup_logs.bat --info  # Check log status
```

### Adding New Components

- **Application logic**: Add to `app_components/`
- **Tests**: Add to `tests/`
- **User tools**: Add to `tools/`
- **Maintenance scripts**: Add to `scripts/maintenance/`
- **Documentation**: Add to `docs/`

## File Naming Conventions

- **Batch files**: Use descriptive names with `.bat` extension
- **Python modules**: Use snake_case naming
- **Configuration files**: Follow tool conventions (e.g., `mypy.ini`)
- **Documentation**: Use descriptive names with `.md` extension

## Path References

When referencing paths in scripts or documentation:

- Use relative paths from project root
- Use forward slashes in documentation (universal)
- Use backslashes in Windows batch files
- Always test path references on target platforms

---

*For historical information about the organization improvements made to achieve this structure, see [archived/organization_summary.md](archived/organization_summary.md).*
