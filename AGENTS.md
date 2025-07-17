# AGENTS Instructions for Casino Event Calendar

These guidelines outline how to format code and validate changes for this Dash
application. See the **Contributing** section in `README.md` for workflow tips
and a link to the project's Git cheat‑sheet.  Codex agents should keep commits
atomic, include a clear summary and ensure automated checks run before pushing.

Directory-specific instructions can be found in
`app_components/AGENTS.md` and `assets/styles/AGENTS.md`.

## Key folders

The repository stores supporting material in dedicated folders:

- `app_components/`  Python modules including callbacks and utilities
- `data/`            CSV event files
- `docs/`            project documentation
- `deploy/`          Render configuration
- `scripts/`         utility scripts such as `setup.sh`
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
- Compile SCSS with `npm run build:css` and watch with `npm run watch:css`.
- Run `npx stylelint "assets/**/*.scss"` before committing style changes.

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

### Run with Gunicorn (as in `deploy/Procfile`)

```bash
gunicorn app:server
```

## Testing and future improvements

- Run `pytest` to execute the unit test suite.
- When adding features include sample data and verify timezone normalization.

—
*[End of AGENTS guidelines]*
