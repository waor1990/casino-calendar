# 🎰 Casino Calendar App — Developer Handoff

## 📌 Overview

A responsive Dash web application that visualizes casino events in a calendar layout.
Built with Plotly Dash (Python 3.11, Node 22) and deployed on Render.

The weekly view is rendered using a CSS grid while day modals are generated with
absolute positioning.  Callback functions in `casino_calendar.dash_app/callbacks/` wire up the interactive elements and keep state in Dash stores.

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

src/casino_calendar/
├── dash_app/                # Dash app package
│   ├── app.py               # create_dash_app() factory
│   ├── callbacks/           # Modular callback handlers
│   ├── data/                # CSV loader, repositories, transforms
│   ├── layout/              # Layout factory and component helpers
│   ├── services/            # Layout/callback utilities
│   └── visualization/       # Plotly chart builders
├── logging/                 # Logging configuration & rotation
├── services/                # Shared services (config cache, colours)
└── settings.py              # Environment + path helpers

assets/
├── styles/index.scss        # Sass entry point
├── styles/partials/         # Modular SCSS partials
├── scripts/theme-toggle.js  # Theme toggle helper
└── dist/style.css           # Generated CSS output

data/
├── raw/casino_events.csv    # Primary dataset
├── lookups/                 # Lookup JSON tables
└── cache/                   # Runtime cache placeholder

config/formatting/.isort.cfg # Import sorter config
config/linting/.flake8       # Flake8 configuration
config/linting/.stylelintrc.json # Stylelint rules
config/typing/mypy.ini       # Static typing configuration

scripts/
├── python/                  # Python maintenance utilities
├── shell/                   # Bash helpers (setup/test)
├── node/                    # Scriptable/Node utilities
└── windows/                 # Windows launchers

deploy/                      # Procfile, render.yaml, gunicorn.conf.py
requirements.txt             # Python dependencies
package.json                 # Node & Sass tooling
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
