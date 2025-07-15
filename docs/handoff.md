# 🎰 Casino Calendar App — Developer Handoff

## 📌 Overview

A responsive Dash web application that visualizes casino events in a calendar layout.
Built with Plotly Dash and deployed on Render.

The weekly view is rendered using a CSS grid while day modals are generated with
absolute positioning.  Callbacks in `callbacks.py` wire up the interactive
elements and keep state in Dash stores.

---

### ✅ Current Features

- 📆 Weekly event chart with labeled time blocks
- 🗂️ Built-in grid calendar view using CSS Grid
- 🧠 Modal views for detailed day and event info
- 🌀 Toggle to display long-spanning events
- 📱 Responsive design across mobile, tablet and desktop
- 🖼️ Custom CSS variables and layout utilities
- 🏷️ Auto-categorizes offer types (Free-Play, Drawings, Giveaways)

---

### 📁 Project Structure Highlights

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
│   └── styles/
│       ├── animations.css     # Keyframes and transitions
│       ├── calendar_grid.css  # Grid layout styles
│       ├── components.css     # Event blocks and utilities
│       ├── layout.css         # Page structure
│       ├── modal.css          # Modal windows
│       └── utilities.css      # Helper classes
├── data/
│   └── casino_events.csv
├── deploy/
│   ├── Procfile                 # Render deployment file
│   └── render.yaml
├── scripts/
│   └── setup.sh
├── requirements.txt
├── app.py                   # Dash entry point
└── README.md

---

## 🧠 Recent Refactors

### CSS Modularization

- Styles moved into `assets/styles/` with `base.css` at the root

### Week Grid Layout

- `week_grid_layout.py` renders the default CSS grid calendar

### Scrollable Body

- `.calendar-scroll-body` scrolls content beneath the sticky header

### Modal architecture

Two modal types exist: `event-modal` and `day-modal`.  Each is toggled via
callbacks and hidden/shown by adding the `modal` CSS class.  Content for the day
modal is built by `generate_day_view_html` in `plotting.py`.

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
- Execute `scripts/test.sh` or run `pytest -q` to verify functionality before
  pushing changes.

---

## 🚀 Deployment

- Platform: [Render.com](https://render.com)
- URL: [https://casino-calendar.onrender.com](https://casino-calendar.onrender.com)
- Python 3.11 / Dash 2.x
- Gunicorn command in `deploy/Procfile`:

```txt
web: gunicorn app:server
```

---

## 🧼 License

Released under [The Unlicense](https://unlicense.org).
