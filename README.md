# 🎰 Casino Event Calendar

A personal Dash application that displays casino events on a responsive calendar. Weekly and daily views include interactive modals and an optional CSS grid preview.

---

## 🚀 Features

- Weekly calendar view with color‑coded event blocks
- Modal windows for detailed event and day information
- Built-in CSS grid layout preview
- Toggle to show or hide the Plotly weekly grid
- Responsive design for desktop, tablet and mobile
- Time zone normalized to Pacific Time (PDT)
- Toggle to show ongoing events that span the week
- Auto-categorizes offer types (Free-Play, Drawings, Giveaways)

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
  week_grid_layout.py    # Grid layout preview using HTML/CSS
assets/                  # Stylesheets (auto-loaded)
  base.css
  layout.css
  components.css
  calendar_grid.css
casino_events.csv        # Event data
requirements.txt         # Python dependencies
Procfile                 # Render deployment
README.md
```

## 🧪 Try It Locally

```bash
python3 -m venv .venv
source .venv/bin/activate  # use .\.venv\Scripts\activate on Windows
pip install -r requirements.txt  # installs black, isort and flake8
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

## 🧼 License

Released under [The Unlicense](https://unlicense.org).
