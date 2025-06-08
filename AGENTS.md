# AGENTS Instructions for Casino Event Calendar

These guidelines outline how to format code and validate changes for this Dash
application.

## Code style

### Python
- Follow PEP 8.
- If available, format using [Black](https://github.com/psf/black):
  ```bash
  black .
  ```
- Optionally sort imports with [isort](https://pycqa.github.io/isort/):
  ```bash
  isort .
  ```
- Optionally lint with [flake8](https://flake8.pycqa.org):
  ```bash
  flake8 .
  ```

### CSS
- Use variables defined in `assets/base.css`.
- Keep styles modular in `assets/*` and avoid global overrides.
- Follow a BEM‑like naming style (e.g., `.week-grid`, `.event-block-grid`).

## Programmatic checks

### Compilation
```bash
python -m py_compile app.py app_components/*.py
```

### Formatting and linting
Run these only if the tools are installed:
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

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org) format, for example:
```text
feat: add Next Week disable logic
fix: correct grid-template-rows calculation
chore: update dependencies
```

## Running locally

### Install requirements
```bash
pip install -r requirements.txt
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
- No unit tests yet—consider adding `pytest` fixtures for `data.py`, `utils.py`, etc.
- When adding features, include sample data and verify timezone normalization.

—
*[End of AGENTS guidelines]*
