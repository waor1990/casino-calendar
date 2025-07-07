# 🎰 Casino Event Calendar

A personal Dash application that displays casino events on a responsive calendar. Weekly and daily views include interactive modals rendered with a CSS grid layout.

---

## 🚀 Features

- Weekly calendar view with color‑coded event blocks
- Modal windows for detailed event and day information
- CSS grid layout for weekly view
- Responsive design for desktop, tablet and mobile
- Time zone normalized to Pacific Time (PDT)
- Toggle to show ongoing events that span the week
- Auto-categorizes offers into Giveaway, Free-Play, Point-Based, Hospitality-Rewards and Special-Events
- SCSS styles compiled with Sass

---

## 📁 Project Layout

```text
app.py                   # Dash entry point
app_components/          # Core logic modules
  callbacks.py           # Dash callbacks
  data.py                # Event data handling
  layout.py              # Layout and modals
  plotting.py            # Plotly figure generation
  utils.py               # Helpers and time zone utilities
  week_grid_layout.py    # CSS-based week grid layout
  legacy.py            # Archived Plotly helpers for reference
assets/                  # Static assets auto-loaded by Dash
  base.css
  style.css
  style.scss
  styles/
    animations.css
    calendar_grid.css
    components.css
    layout.css
    modal.css
    utilities.css
casino_events.csv        # Event data
requirements.txt         # Python dependencies
Procfile                 # Render deployment
package.json           # NPM scripts for Sass
README.md
```

## 🧪 Try It Locally

```bash
python3 -m venv .venv
source .venv/bin/activate  # use .\.venv\Scripts\activate on Windows
./setup.sh                 # install Python and Node dependencies
pip install -r requirements.txt  # installs black, isort and flake8
npm install
npm run build:css
pre-commit install
pre-commit run --all-files
python -m py_compile app.py app_components/*.py
python app.py
```

## 🌍 Deployment

Hosted at [https://casino-calendar.onrender.com](https://casino-calendar.onrender.com)

`Procfile`:

```txt
web: gunicorn app:server
```

## 🤝 Contributing

Please follow the development guidelines in `AGENTS.md` when proposing
changes. Run the formatters and linters before committing and see
`GIT-CHEATSHEET.md` for handy Git commands.

## 🧼 License

Released under [The Unlicense](https://unlicense.org).
