# 🎰 Casino Event Calendar

A personal Dash application that displays casino events on a responsive calendar. Weekly and daily views include interactive modals and an optional CSS grid preview.

---

## 🚀 Features

- Weekly calendar view with color‑coded event blocks
- Modal windows for detailed event and day information
- Optional grid layout preview built with pure CSS
- Responsive design for desktop, tablet and mobile
- Time zone normalized to Pacific Time (PDT)
- Toggle to show ongoing events that span the week

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
  typography.css
casino_events.csv        # Event data
requirements.txt         # Python dependencies
Procfile                 # Render deployment
README.md
```

## 🧪 Try It Locally
```bash
pip install -r requirements.txt
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
