# 🎰 Casino Calendar App — Developer Handoff

## 📌 Overview

A responsive Dash web application that visualizes casino events in a calendar-style layout. Built with Plotly + Dash and deployed to Render.com.

---

## ✅ Current Features

- 📆 Weekly event chart with labeled time blocks
- 📊 Preview calendar using CSS Grid layout
- 📱 Responsive design for mobile/tablet/desktop
- 🖼️ Custom CSS with variables, modular utilities, and layout controls
- 🧠 Modal views for detailed day/event info

---

## 📁 Project Structure Highlights

casino_calendar/
│
├── app_components/
│   ├── layout.py            # Layout structure: sticky header, modals, containers
│   ├── callbacks.py         # All Dash callbacks
│   ├── data.py              # CSV loader with timezone handling
│   ├── plotting.py          # Plotly charting logic (week/day)
│   ├── utils.py             # Responsive calculations and constants
│   ├── week_grid_layout.py  # Preview grid layout using pure CSS
│
├── assets/
│   ├── base.css             # Root variables and resets
│   ├── layout.css           # Scrollable containers and page structure
│   ├── components.css       # Event blocks, buttons, utility classes
│   ├── calendar_grid.css    # Week grid preview CSS layout
│   └── typography.css       # Font styling and text sizes
│
├── casino_events.csv
├── requirements.txt
├── app.py                   # Dash entry point
├── Procfile                 # Render deployment file
└── README.md

---

## 🧠 Recent Refactors

### ✅ CSS Modularization

- `custom.css` split into:
  - `base.css`: color palette, spacing variables
  - `layout.css`: scroll containers, `.main-layout`, `.calendar-content`, etc.
  - `components.css`: modals, buttons, overflow boxes
  - `calendar_grid.css`: `.week-grid`, `.event-block-grid`, `.day-column`, etc.
  - `typography.css`: font size classes, utility text styles

### ✅ Grid Layout Preview

- `week_grid_layout.py` builds a grid-style week calendar
- Injected via Dash into `dev-preview-output` below the weekly chart
- Toggle via `preview-grid-button`

### ✅ Scrollable Body

- `.calendar-scroll-body` allows chart/grid content to scroll below header
- Keeps `sticky-header` + week label fixed at the top

---

## 🛠️ Work in Progress / Next Steps

- 🔄 Convert more layout blocks from Plotly to pure CSS/Grid
- 📱 Polish mobile responsiveness of preview layout
- ♿ Improve accessibility: tab order, ARIA roles
- ✨ Animate modal and overflow transitions more smoothly

---

## 🧪 Testing / Known Fixes

- `KeyError: 7` in grid layout was resolved by clamping day indices between 0–6 ✅
- Week charts now height-responsive based on `usable-height` from window innerHeight ✅
- Scroll logic uses `calendar-scroll-body` height via `100vh - 150px` ✅

---

## 🚀 Deployment

- Platform: [Render.com](https://render.com)
- URL: [https://casino-calendar.onrender.com](https://casino-calendar.onrender.com)
- Python 3.11 / Dash 2.0+
- Gunicorn used in `Procfile`:  

  ```txt
  web: gunicorn app:server
