# Casino Calendar - AI Agent Instructions```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

This is a Dash web application for displaying casino events in a calendar view. The app is designed for Python 3.11 and Node 22 (tested with v22.9.0).```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

**See `.github/copilot-instructions.md` for comprehensive development guidelines.**```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

## Architecture Overview```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

The app follows a modular Dash pattern with clear separation of concerns:```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

- **`app.py`** - Thin entry point importing the Dash factory and exposing {tick}server{tick}.
- **`src/casino_calendar/`** - Application package containing Dash modules, logging, and shared services.
- **`assets/`** - Sass source ({tick}styles/{tick}), compiled CSS ({tick}dist/style.css{tick}), and client scripts.
- **`data/`** - {tick}raw/{tick} CSV input plus lookup JSON in {tick}lookups/{tick}.
- **`tests/`** - Pytest suites grouped by {tick}unit/{tick}, {tick}integration/{tick}, and {tick}e2e/{tick}.
- **`scripts/`** - Runtime-specific tooling ({tick}python/{tick}, {tick}shell/{tick}, {tick}node/{tick}, {tick}windows/{tick}).
- **`config/`** - Configuration split into formatting, linting, and typing subdirectories.
- **`docs/`** - Current documentation plus {tick}docs/legacy/{tick} for historical notes.```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

## Development Workflow```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Quick Setup and Running```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

```cmd
# Windows (recommended approach)
tools\setup.bat      # Creates venv, installs dependencies, builds CSS
tools\run_direct.bat # Launches app with proper environment```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

# Or use convenience launchers
setup.bat  # calls tools\setup.bat
run.bat    # calls tools\run_direct.bat
``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### VS Code Tasks```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

Use the predefined tasks for common operations:```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

- "Run Casino Calendar App" - Background server with logging
- "Run Tests" - Execute pytest suite
- "Install Dependencies" - Update Python packages```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

## Key Patterns```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Data Flow```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

Events load from `data/casino_events.csv` → `load_event_data()` in `data.py` → UI layout generation → interactive callbacks```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Callback Organization```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

Callbacks are split by domain and centrally registered:```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

- `callbacks/events.py` - Modal dialogs and event interactions
- `callbacks/filters.py` - Casino filtering and date range selection
- `callbacks/theme.py` - Theme switching functionality```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Logging System```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

Use `setup_logger(__name__)` in all modules. Control via environment variables:```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

- `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR)
- `LOG_FILE` for optional file output```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

## Code style```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Python```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

- Follow PEP 8.
- Format using [Black](https://github.com/psf/black):```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

  ```bash
  black .
  ``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

- Sort imports with [isort](https://pycqa.github.io/isort/):```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

  ```bash
  isort --settings-path config/formatting/.isort.cfg .
  ``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

- Lint with [flake8](https://flake8.pycqa.org):```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

  ```bash
  flake8 --config config/linting/.flake8 .
  ``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

These tools are installed via `requirements.txt`.```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### CSS```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

**⚠️ CRITICAL WARNING: NEVER modify `assets/dist/style.css` directly! It is auto-generated.**```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

- **ALL CSS changes must be made in SCSS files** in `assets/styles/` directory
- The `style.css` file is automatically generated and will be overwritten
- Use variables defined in `_variables.scss` (not `assets/base.css`)
- Keep styles modular and avoid global overrides
- Follow a BEM‑like naming style (e.g., `.week-grid`, `.event-block-grid`)
- Compile SCSS with `npm run build:css` and watch with `npm run watch:css`
- Run `npm run lint:css` before committing style changes
- **Remember: Any direct edits to `style.css` will be lost on next build**```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

## Programmatic checks```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

Run `scripts/shell/test.sh` before committing to execute static analysis and the test
suite.  The script wraps the commands below.```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Compilation```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

```bash
python -m py_compile app.py casino_calendar.dash_app/*.py
``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Formatting and linting```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

Run these only if the tools are installed.  Consider installing optional tools
such as `mypy`, `bandit` and `pydocstyle` for additional checks:```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

```bash
black --check .
isort --check-only .
flake8 .
``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

If the commands are missing, skip them and proceed.```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

## Pull request message```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Title```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

- Use an imperative title prefixed with a Conventional Commit type (`feat:`, `fix:`, `chore:`).```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Description```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

- Reference related issues when applicable.
- Summarize changes in bullet points.
- Describe testing steps and results.
- Add screenshots or GIFs for visual changes.```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Branch naming```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

Use prefixes to categorize work:```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

- `feature/` for new features
- `fix/` for bug fixes
- `refactor/` for restructuring
- `test/` for test-only updates
- `doc/` for documentation changes```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

## Commit messages```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

Use [Conventional Commits](https://www.conventionalcommits.org) format, for example:```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

```text
feat: add Next Week disable logic
fix: correct grid-template-rows calculation
chore: update dependencies
``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

---```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

## Automatic Branch Cleanup *(New)*```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

After successfully merging a pull request into the `main` branch:```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

## **Immediately delete remote feature branches**```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

```bash
git push origin --delete <feature-branch-name>
``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

- **Update local repositories** to reflect remote deletions:```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

```bash
git fetch --prune
``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Example```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

If the merged branch was `codex/update-readme.md`:```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

```bash
git push origin --delete codex/update-readme.md
git fetch --prune
``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

---```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

## Running locally```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Create a virtual environment```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

```bash
python3 -m venv .venv
source .venv/bin/activate  # on Windows use .\.venv\Scripts\activate
``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Install requirements```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

```bash
scripts/setup.sh           # installs Python and Node deps
pip install -r requirements.txt
npm install
npm run build:css
``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

Run the formatters and linter:```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

```bash
black . && isort . && flake8 .
``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Enable pre-commit hooks```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Start in development mode```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

```bash
python app.py
``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

### Run with Gunicorn (as in `Procfile`)```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

```bash
gunicorn app:server
``````cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

## Testing and future improvements```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

- Run `pytest` to execute the unit test suite.
- When adding features include sample data and verify timezone normalization.```cmd
# Windows (recommended approach)
scripts\windows\setup.bat      # Creates venv, installs dependencies, builds CSS
scripts\windows
un_direct.bat # Launches app with proper environment

# Or use convenience launchers
setup.bat  # calls scripts\windows\setup.bat
run.bat    - calls scripts\windows
un_direct.bat
```

—
*[End of AGENTS guidelines]*
