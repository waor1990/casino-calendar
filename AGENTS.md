# AGENTS Instructions for Casino Event Calendar

Guidelines for contributing, styling, and validating changes to this Dash + Plotly app.

## Code style

**Python**  
- Follow PEP 8.  
- Format via [Black](https://github.com/psf/black):
  ```bash
  black .
  ```
- Sort imports via [isort](https://pycqa.github.io/isort/):
  ```bash
  isort .
  ```
- Lint with [flake8](https://flake8.pycqa.org):
  ```bash
  flake8 .
  ```

**CSS**

- Use variables in `assets/base.css`.
- Follow modular files in `assets/*` (no global overrides).
- Keep selectors in a BEM-like style (e.g., `.week-grid`, `.event-block-grid`).

## Programmatic check

**Compilation**
```bash
python -m py_compile app.py app_components/*.py
```

**Formatting check**
```bash
black --check .
isort --check-only .
```

**Linting**
```bash
flake8 .
```

## Pull request message

**Title**

- Imperative and descriptive (e.g., `feat: add week-offset boundary logic`)
- Prefix with Conventional Commit type (`feat:`, `fix:`, `chore:`)

**Description**

- Reference any related issue (e.g., `Closes #42`).
- Bullet-point summary of changes.
- Testing steps & results (compilation, lint, manual UI checks).
- Attach screenshots or GIFs for visual updates.

## Commit messages

Adopt [Conventional Commits](https://www.conventionalcommits.org):
```text
feat: add Next Week disable logic
fix: correct grid-template-rows calculation
chore: update dependencies
```

## Running Locally

**Install requirements**
```bash
pip install -r requirements.txt
```

**Start in dev mode**
```bash
python app.py
```

**Or test with Gunicorn (as in `Procfile`)**
```bash
gunicorn app:server
```

## Testing & Future Improvements

- Currently no unit tests—consider adding `pytest` fixtures for `data.py`, `utils.py`, etc.
- When adding new features, include small sample data and verify timezone normalization.

—
*[End of AGENTS guidelines]*
