# 🎰 Casino Event Calendar

A personal Dash application that displays casino events on a responsive calendar.
Weekly and daily views include interactive modals rendered with a CSS grid layout.

The project targets **Python 3.11** and **Node 18**.  Other versions may work
but are not tested.

---

## 🚀 Features

- Weekly calendar view with color‑coded event blocks
- Modal windows for detailed event and day information
- CSS grid layout for weekly view
- Responsive design for desktop, tablet and mobile
- Times stored in UTC and displayed in Pacific Time (PDT)
- Toggle to show ongoing events that span the week
- Auto-categorizes offers into Giveaway, Free-Play, Point-Based, Hospitality-Rewards and Special-Events
- SCSS styles compiled with Sass

---

## 📁 Project Layout

```text
app.py                   # Dash entry point
app_components/          # Core logic modules
  callbacks/             # Dash callback handlers
  utils/                 # Shared helper functions
assets/                  # Static assets auto-loaded by Dash
data/                    # CSV data files
  casino_events.csv
docs/                    # Project documentation
  handoff.md
  TODO.md
  legacy_plotly.md       # Archived Plotly helpers
deploy/                  # Deployment configuration
  Procfile
  render.yaml
scripts/                 # Utility scripts
  setup.sh
requirements.txt         # Python dependencies
package.json             # NPM scripts for Sass
```

## 🧪 Try It Locally

```bash
python3 -m venv .venv
source .venv/bin/activate  # use .\.venv\Scripts\activate on Windows
scripts/setup.sh                 # install Python and Node dependencies
npm install
npm run build:css  # compiles assets/style.scss to assets/style.css
npm run lint:css
pip install -r requirements.txt
pre-commit install
pre-commit run --all-files
python -m py_compile app.py app_components/*.py
scripts/test.sh                  # run linters and tests
python app.py
```

On Windows you can run everything from one command by executing `run.bat`
in a Command Prompt or the VSCode terminal:

```cmd
run.bat
```

## 🌍 Deployment

Hosted at [https://casino-calendar.onrender.com](https://casino-calendar.onrender.com)

`deploy/Procfile`:

```txt
web: gunicorn app:server
```

## 🤝 Contributing

Please follow the development guidelines in `AGENTS.md` when proposing
changes. Run the formatters and linters before committing and see
`GIT-CHEATSHEET.md` for handy Git commands.
VSCode users can take advantage of the included `.editorconfig` and
`.vscode` files so formatting and linting run automatically on save.

### Branch strategy

Use prefix-based branches when contributing:

- `feature/` for new functionality
- `fix/` for bug fixes
- `refactor/` for internal improvements
- `test/` for test additions
- `doc/` for documentation updates

## 🧼 License

Released under [The Unlicense](https://unlicense.org).
