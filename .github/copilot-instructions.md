# Casino Calendar - Copilot Instructions

This is a Dash web application for displaying casino events in a calendar view. The app is designed for Python 3.11 and Node 18.

## Architecture Overview

The app follows a modular Dash pattern:

- **`app.py`** - Entry point that loads data, creates layout, and registers callbacks
- **`app_components/`** - Core application modules with separation of concerns:
  - `layout.py` - Main UI layout generation
  - `callbacks/` - Event handlers split by domain (events, filters, theme)
  - `data.py` - CSV data loading and processing
  - `logging_config.py` - Centralized logging setup
- **`utils/`** - Shared utilities (colors, data parsing, log rotation)
- **`assets/`** - Static assets with SCSS compilation to CSS

## Key Patterns

### Data Flow

Events are loaded from `data/casino_events.csv` into a pandas DataFrame with columns: EventName, Casino, Location, Offer, StartDate, EndDate. The data flows through:

1. `load_event_data()` in `data.py` - CSV parsing and datetime conversion
2. `create_layout()` in `layout.py` - UI generation with event data
3. Callback functions in `callbacks/` - Interactive updates

### Callback Organization

Callbacks are split across modules and registered via `register_callbacks()`:

- `callbacks/events.py` - Modal dialogs and event interactions
- `callbacks/filters.py` - Casino filtering and date range selection
- `callbacks/theme.py` - Theme switching functionality

### Color System

Casino colors are managed through JSON files in `data/`:

- `casino_colors.json` - Casino-specific color mappings
- `default_colors.json` - Fallback color palette
- Access via `utils.colors.get_color(casino_name)`

### Logging

Comprehensive logging system using `app_components.logging_config`:

- Environment variable `LOG_LEVEL` controls verbosity (DEBUG, INFO, WARNING, ERROR)
- Optional file logging via `LOG_FILE` environment variable
- All modules use `setup_logger(__name__)` for consistent formatting

## Development Workflow

### Setup and Running

```cmd
# Windows (recommended)
tools\setup.bat      # Creates venv, installs dependencies, builds CSS
tools\run_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls tools\setup.bat
run.bat    # calls tools\run_direct.bat
```

### CSS/SCSS Development

**⚠️ CRITICAL: NEVER modify `assets/style.css` directly! It is auto-generated and will be overwritten.**

- **ALL CSS changes must be made in SCSS files** in `assets/styles/` directory
- SCSS files compile to `assets/style.css` automatically when the app runs
- Use `npm run watch:css` for auto-compilation during development
- Always run `npm run build:css` before committing
- Follow BEM-like naming (`.week-grid`, `.event-block-grid`)
- The `style.css` file is generated - any direct edits will be lost

### Testing and Quality

- Run `scripts/test.sh` before commits (wraps linting and tests)
- Python: Black formatting, isort imports, flake8 linting
- CSS: stylelint with config in `config/.stylelintrc.json`
- Tests in `tests/` use pytest with fixtures in `conftest.py`

### VS Code Tasks

Use the predefined tasks:

- "Run Casino Calendar App" - Background server with logging
- "Run Tests" - Execute pytest suite
- "Install Dependencies" - Update Python packages

## Project Conventions

### File Organization

- Configuration files centralized in `config/` (`.flake8`, `.isort.cfg`, `mypy.ini`)
- Documentation in `docs/` with archived completed docs in `docs/archived/`
- User-facing tools in `tools/` with root-level convenience launchers
- Log files in `logs/` with automatic archiving

### Import Style

- Use relative imports within `app_components/`
- Import utilities with full paths: `from utils.colors import get_color`
- Type hints preferred, especially for function signatures

### Error Handling

- Use structured logging for errors with context
- Graceful fallbacks for missing data files (see `utils/colors.py`)
- Exception logging includes stack traces via `exc_info=True`

## Common Operations

### Adding New Callbacks

1. Create callback function in appropriate `callbacks/` module
2. Add registration call to module's `register_callbacks()` function
3. Import and call in `callbacks/__init__.py`

### Modifying Data Structure

1. Update CSV headers in `data/casino_events.csv`
2. Modify parsing logic in `app_components/data.py`
3. Update affected layout and callback functions
4. Add/update tests in `tests/`

### Styling Changes

**⚠️ WARNING: Never edit `assets/style.css` directly - it's auto-generated!**

1. Edit SCSS files in `assets/styles/` directory only
2. Use variables from `_variables.scss` and mixins from `_mixins.scss`
3. Compile with `npm run build:css` (happens automatically when app runs)
4. Test responsive behavior across device sizes
5. Remember: `style.css` is overwritten on every build - SCSS changes only!
