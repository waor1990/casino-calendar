# AGENTS instructions for `app_components`

This directory contains the Python modules for the Dash application.

- Follow the style and tooling described in the repository root `AGENTS.md`.
- Keep functions small and focused with type hints and docstrings.
- Avoid side effects and prefer returning new values over mutating arguments.
- `legacy.py` contains deprecated Plotly helpers for reference only.
- Split out helpers if a file grows beyond roughly 400 lines.
- Check syntax before committing:

  ```bash
  python -m py_compile *.py
  ```

*[End of app_components guidelines]*
