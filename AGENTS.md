# Casino Calendar – Agent Notes

Follow these project-wide conventions when working in this repository.

## Repository layout
- Python application code lives under `src/casino_calendar/`. Prefer package imports over ad-hoc filesystem access.
- Dash entry points are `app.py` and `wsgi.py`; keep configuration changes centralized rather than duplicating settings.
- Documentation lives in `docs/` with onboarding in `README.md` and `QUICKSTART.md`.

## Development practices
- Target Python 3.11 syntax (including PEP 604 unions) and avoid wrapping imports in `try/except` blocks.
- Initialize loggers with `casino_calendar.logging.config.setup_logger(__name__)` for new modules to keep logging consistent.
- Keep user-facing behaviour changes accompanied by documentation updates in the relevant guide.
- Default to `scripts/shell/test.sh` for full verification during development.

## Frontend assets
- Do not edit `assets/dist/style.css` directly. Update SCSS under `assets/styles/` and rebuild with `npm run build:css` (or `npm run watch:css` during development).
- Use the Stylelint configs in `config/linting` via `npm run lint:css` when touching styles.
- Node tooling is pinned to the version in `package.json`/`volta`; avoid introducing tools that conflict with it.

## Testing and quality checks
- Run `black`, `isort`, and `flake8` before committing. Prefer running `scripts/shell/test.sh` for a single entry point.
- Execute `pytest` for Python changes and `npm run lint:css` when styles are modified.
- Clean up build/test artifacts before committing.

## Security and hygiene
- Never commit `.env` files or other credentials. Keep environment-specific secrets in deployment configuration, not source control.
- Avoid leaking private data in tests, fixtures, or documentation examples.

## Pull requests
- Summarize impacted modules, list verification steps (linting/tests), and mention documentation updates in your PR description.
- Reference relevant context from `docs/` when explaining behaviour changes.

## Commit formatting
- Follow Conventional Commit syntax: `<type>(<scope>): <subject>` using lower-case subjects.
- Use one of the allowed types from `commitlint.config.js` (`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `merge`, `revert`).
- Choose a non-empty scope from `commitlint.config.js` (e.g., `app`, `layout`, `styles`, `data`, `scripts`, `tests`, `docs`, `infra`).
- Keep subjects concise (≤72 characters) and avoid trailing punctuation.
