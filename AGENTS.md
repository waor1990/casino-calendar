# Casino Calendar - AI Agent Instructions

This is a Dash web application for displaying casino events in a calendar view. The app is designed for Python 3.11 and Node 18.

**See `.github/copilot-instructions.md` for comprehensive development guidelines.**

## Architecture Overview

The app follows a modular Dash pattern with clear separation of concerns:

- **`app.py`** - Entry point that loads data, creates layout, and registers callbacks
- **`app_components/`** - Core application modules (layout, callbacks, data processing, logging)
- **`utils/`** - Shared utilities (colors, data parsing, log rotation)
- **`assets/`** - Static assets with SCSS compilation to CSS
- **`data/`** - CSV event data and JSON configuration files
- **`tests/`** - Test suite with pytest fixtures
- **`tools/`** - User-facing scripts for setup and running
- **`config/`** - Tool configuration files (.flake8, .isort.cfg, etc.)
- **`scripts/`** - Utility and maintenance scripts
- **`docs/`** - Project documentation with archived completed docs

## Development Workflow

### Quick Setup and Running

```cmd
# Windows (recommended approach)
tools\setup.bat      # Creates venv, installs dependencies, builds CSS
tools\run_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls tools\setup.bat
run.bat    # calls tools\run_direct.bat
```

### VS Code Tasks

Use the predefined tasks for common operations:

- "Run Casino Calendar App" - Background server with logging
- "Run Tests" - Execute pytest suite
- "Install Dependencies" - Update Python packages

## Key Patterns

### Data Flow

Events load from `data/casino_events.csv` → `load_event_data()` in `data.py` → UI layout generation → interactive callbacks

### Callback Organization

Callbacks are split by domain and centrally registered:

- `callbacks/events.py` - Modal dialogs and event interactions
- `callbacks/filters.py` - Casino filtering and date range selection
- `callbacks/theme.py` - Theme switching functionality

### Logging System

Use `setup_logger(__name__)` in all modules. Control via environment variables:

- `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR)
- `LOG_FILE` for optional file output

## Code style

### Python

- Follow PEP 8.
- Format using [Black](https://github.com/psf/black):

  ```bash
  black .
  ```

- Sort imports with [isort](https://pycqa.github.io/isort/):

  ```bash
  isort --settings-path config/.isort.cfg .
  ```

- Lint with [flake8](https://flake8.pycqa.org):

  ```bash
  flake8 --config config/.flake8 .
  ```

These tools are installed via `requirements.txt`.

### CSS

**⚠️ CRITICAL WARNING: NEVER modify `assets/style.css` directly! It is auto-generated.**

- **ALL CSS changes must be made in SCSS files** in `assets/styles/` directory
- The `style.css` file is automatically generated and will be overwritten
- Use variables defined in `_variables.scss` (not `assets/base.css`)
- Keep styles modular and avoid global overrides
- Follow a BEM‑like naming style (e.g., `.week-grid`, `.event-block-grid`)
- Compile SCSS with `npm run build:css` and watch with `npm run watch:css`
- Run `npm run lint:css` before committing style changes
- **Remember: Any direct edits to `style.css` will be lost on next build**

## Programmatic checks

Run `scripts/test.sh` before committing to execute static analysis and the test
suite.  The script wraps the commands below.

### Compilation

```bash
python -m py_compile app.py app_components/*.py
```

### Formatting and linting

Run these only if the tools are installed.  Consider installing optional tools
such as `mypy`, `bandit` and `pydocstyle` for additional checks:

```bash
black --check .
isort --check-only .
flake8 .
```

If the commands are missing, skip them and proceed.

## Pull request message

### Title

- Use an imperative title prefixed with a Conventional Commit type (`feat:`, `fix:`, `chore:`).

### Description

- Reference related issues when applicable.
- Summarize changes in bullet points.
- Describe testing steps and results.
- Add screenshots or GIFs for visual changes.

### Branch naming

Use prefixes to categorize work:

- `feature/` for new features
- `fix/` for bug fixes
- `refactor/` for restructuring
- `test/` for test-only updates
- `doc/` for documentation changes

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org) format, for example:

```text
feat: add Next Week disable logic
fix: correct grid-template-rows calculation
chore: update dependencies
```

---

## Automatic Branch Cleanup *(New)*

After successfully merging a pull request into the `main` branch:

## **Immediately delete remote feature branches**

```bash
git push origin --delete <feature-branch-name>
```

- **Update local repositories** to reflect remote deletions:

```bash
git fetch --prune
```

### Example

If the merged branch was `codex/update-readme.md`:

```bash
git push origin --delete codex/update-readme.md
git fetch --prune
```

---

## Running locally

### Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # on Windows use .\.venv\Scripts\activate
```

### Install requirements

```bash
scripts/setup.sh           # installs Python and Node deps
pip install -r requirements.txt
npm install
npm run build:css
```

Run the formatters and linter:

```bash
black . && isort . && flake8 .
```

### Enable pre-commit hooks

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### Start in development mode

```bash
python app.py
```

### Run with Gunicorn (as in `Procfile`)

```bash
gunicorn app:server
```

## Testing and future improvements

- Run `pytest` to execute the unit test suite.
- When adding features include sample data and verify timezone normalization.

—
*[End of AGENTS guidelines]*
