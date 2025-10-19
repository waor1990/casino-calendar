# Casino Calendar – Agent Notes

Welcome to the Casino Calendar project. Follow these guidelines when making changes:

1. **Source layout** – Python code lives under `src/casino_calendar/`. Use module imports rather than relative filesystem paths.
2. **Documentation** – Update `README.md` and the relevant guide under `docs/` whenever behaviour or configuration changes.
3. **Assets** – Never edit `assets/dist/style.css` directly. Modify the SCSS files under `assets/styles/` and rebuild with `npm run build:css`.
4. **Python style** – Run `black`, `isort`, and `flake8` before committing. Type hints should use Python 3.11 syntax (PEP 604 unions, etc.). Avoid adding `try/except` around imports.
5. **Testing** – Execute `scripts/shell/test.sh` (or at minimum `pytest`) before submitting a PR. Dash integration tests require Chrome/Chromedriver.
6. **Logging** – Use `casino_calendar.logging.config.setup_logger(__name__)` for new modules so logging configuration remains consistent.
7. **Secrets** – Do not commit `.env` files or production credentials. Environment-specific overrides belong in deployment configuration, not the repository.

Pull requests should describe the change, reference impacted modules, and list verification steps (linting/tests). Use the documentation set in `docs/` for additional context.
