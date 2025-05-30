# 🎰 Casino Event Calendar

A personal-use Dash app that visualizes casino events on a responsive calendar. Weekly and day views with interactive modals, customizable layout, and preview mode.

---

## 🚀 Features

- View casino events in weekly blocks
- Click to open modal with details or daily breakdown
- Optional preview: grid-based layout using CSS
- Responsive to screen size (desktop/mobile/tablet)
- Color-coded by casino with auto-generated legend
- Time zone normalized to Pacific Time (PDT)

---

## 📁 Project Layout

```text
casino_calendar/
├── app.py                   # Main Dash entry
├── app_components/          # Core logic modules
│   ├── callbacks.py         # Dash callbacks
│   ├── data.py              # Event data handling
│   ├── layout.py            # Main layout + header + modals
│   ├── plotting.py          # Plotly figure generation
│   ├── utils.py             # Layout utilities, time zones
│   └── week_grid_layout.py  # Grid layout preview using HTML/CSS
│
├── assets/                  # All stylesheets (auto-loaded)
│   ├── base.css
│   ├── layout.css
│   ├── components.css
│   ├── calendar_grid.css
│   └── typography.css
│
├── casino_events.csv        # Event data
├── requirements.txt         # Pip dependencies
├── Procfile                 # Render deployment
└── README.md

## 🧪 Try It Locally
bash
Copy
Edit
pip install -r requirements.txt
python app.py

## 🌍 Deployment

Hosted on Render:

🔗 https://casino-calendar.onrender.com

Procfile:

txt
Copy
Edit
web: gunicorn app:server

## 🧼 License

MIT — free for personal use and modification.

vbnet
Copy
Edit
