# 🎰 Casino Calendar App — Developer Handoff

## 📌 Overview

A responsive Dash web application that visualizes casino events in a calendar layout. Built with Plotly Dash and deployed on Render.

---

## ✅ Current Features

- 📆 Weekly event chart with labeled time blocks
- 📊 Toggleable grid calendar preview using CSS Grid
- 🔄 Toggle to hide or show the Plotly weekly grid
- 🧠 Modal views for detailed day and event info
- 🌀 Toggle to display long-spanning events
- 📱 Responsive design across mobile, tablet and desktop
- 🖼️ Custom CSS variables and layout utilitiess

---

## 📁 Project Structure Highlights

yaml
casino_calendar/
├── app_components/
│   ├── layout.py            # Sticky header, modals, containers
│   ├── callbacks.py         # Dash callbacks
│   ├── data.py              # CSV loader with timezone handling
│   ├── plotting.py          # Plotly charting logic
│   ├── utils.py             # Responsive calculations
│   └── week_grid_layout.py  # Pure CSS grid preview
├── assets/
│   ├── base.css             # Variables and resets
│   ├── layout.css           # Page structure
│   ├── components.css       # Event blocks and utilities
│   ├── calendar_grid.css    # Grid layout styles
│   └── typography.css       # Fonts and text sizes
├── casino_events.csv
├── requirements.txt
├── app.py                   # Dash entry point
├── Procfile                 # Render deployment file
└── README.md

---

## 🧠 Recent Refactors

### CSS Modularization

- Split former `custom.css` into `base.css`, `layout.css`, `components.css`, `calendar_grid.css` and `typography.css`

### Grid Layout Preview

- `week_grid_layout.py` renders a grid-style week calendar
- Injected into `dev-preview-output` and toggled via `preview-grid-button`

### Scrollable Body

- `.calendar-scroll-body` scrolls content beneath the sticky header

---

## 🛠️ Work in Progress / Next Steps

- Convert more layout blocks from Plotly to pure CSS/Grid
- Polish mobile responsiveness
- Improve accessibility: tab order and ARIA roles
- Smooth modal and overflow transitions

---

## 🧪 Testing / Known Fixes

- `KeyError: 7` fixed by clamping day indices when building grid layout
- Week charts adjust height based on `usable-height`
- Scroll logic uses `calendar-scroll-body` height via `100vh - 150px`

---

## 🚀 Deployment

- Platform: [Render.com](https://render.com)
- URL: [https://casino-calendar.onrender.com](https://casino-calendar.onrender.com)
- Python 3.11 / Dash 2.x
- Gunicorn command in `Procfile`:

```txt
web: gunicorn app:server
```

---

## 🧼 License

Released under [The Unlicense](https://unlicense.org).
