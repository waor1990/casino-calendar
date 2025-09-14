# 🎰 Casino Calendar App — Developer Handoff

## 📌 Overview

A responsive Dash web application that visualizes casino events in a calendar layout.
Built with Plotly Dash (Python 3.11, Node 22) and deployed on Render.

The weekly view is rendered using a CSS grid while day modals are generated with
absolute positioning.  Callback functions in `app_components/callbacks/` wire up the interactive elements and keep state in Dash stores.

---

### ✅ Current Features

- 📆 Weekly event chart with labeled time blocks
- 🗂️ Built-in grid calendar view using CSS Grid
- 🧠 Modal views for detailed day and event info
- 🌀 Toggle to display long-spanning events
- 📱 Responsive design across mobile, tablet and desktop
- 🖼️ Custom CSS variables and layout utilities
- 🏷️ Auto-categorizes offers (Giveaway, Free-Play, Point-Based, Hospitality-Rewards, Special-Events)
- 🛎️ Hotel booking links when a casino is selected
- 🪵 Comprehensive logging system for debugging and monitoring

---

### 📁 Project Structure Highlights

casino_calendar/
├── app.py                   # Dash entry point
├── app_components/          # Layout, callbacks and helpers
│   ├── callbacks/           # Modular callback handlers
│   ├── data.py              # CSV loader with timezone handling
│   ├── layout.py            # Sticky header, modals, containers
│   ├── plotting.py          # Legacy Plotly helpers and modal builders
│   └── week_grid_layout.py  # Pure CSS grid preview
├── assets/                  # Static assets
│   ├── base.css             # Variables and resets
│   ├── style.scss           # SCSS entry (compiled to style.css)
│   ├── style.css            # Auto-generated CSS
│   └── styles/              # SCSS partials
├── config/                  # Tool configuration files
├── data/
│   └── casino_events.csv
├── docs/                    # Project documentation
├── scripts/
│   └── setup/               # Installation scripts
│       └── setup.sh
├── tools/                   # User-facing batch files
│   ├── cleanup_logs.bat
│   ├── run_direct.bat
│   └── setup.bat
├── tests/                   # Test suite
├── utils/                   # Shared utilities
├── Procfile                 # Gunicorn deployment configuration
├── render.yaml              # Render.com deployment file
└── requirements.txt

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
  - Gunicorn command in `Procfile`:

```txt
web: gunicorn app:server
```

---

## 🧼 License

Released under [The Unlicense](https://unlicense.org).
