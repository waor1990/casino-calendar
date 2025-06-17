# AGENTS Instructions for Casino Event Calendar

These guidelines outline how to format code and validate changes for this Dash
application.

## Code style

### Python

- Follow PEP 8.
- Format using [Black](https://github.com/psf/black):

  ```bash
  black .
  ```

- Sort imports with [isort](https://pycqa.github.io/isort/):

  ```bash
  isort .
  ```

- Lint with [flake8](https://flake8.pycqa.org):

  ```bash
  flake8 .
  ```

These tools are installed via `requirements.txt`.

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
pip install -r requirements.txt
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

- No unit tests yet—consider adding `pytest` fixtures for `data.py`, `utils.py`, etc.
- When adding features, include sample data and verify timezone normalization.

—
*[End of AGENTS guidelines]*
