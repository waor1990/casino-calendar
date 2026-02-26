# Casino Calendar – Developer Handoff Guide

## 📌 Overview

Casino Calendar is a responsive Dash web application that visualises casino events in a weekly calendar. The layout is rendered with Dash components, CSS Grid, and Plotly figures for interactive overlays. The project targets **Python 3.11** and **Node 22** and is currently deployed to Render.

---

## ✅ Current Feature Set

- 📆 Weekly event grid with colour-coded time blocks
- 🗂️ Casino and offer-type filters backed by Dash stores
- 🧠 Day and event modals with rich details and hotel booking helper content
- 🌀 Toggle for displaying long-running events that span multiple days
- 📱 Responsive design tuned for desktop, tablet, and mobile breakpoints
- 🌗 Persistent light/dark theme toggle driven by Dash stores and client-side JS, presented as a floating action button in the top-right corner
- 🏷️ Automatic offer categorisation based on keyword analysis
- 🛎️ Hotel booking links surfaced when a casino is selected from the legend
- 🪵 Structured logging with rotation, HTTP log routing, and maintenance scripts

---

## 📁 Key Modules (Quick Reference)

```plaintext
src/casino_calendar/
├── dash_app/
│   ├── app.py              # create_dash_app factory and run_app helper
│   ├── callbacks/
│   │   ├── events.py       # Modal logic, overflow toggles, pattern-matching callbacks
│   │   ├── filters.py      # Casino and offer filter state
│   │   ├── navigation.py   # Week navigation controls and scroll helpers
│   │   └── theme.py        # Light/dark theme toggle and client-side sync
│   ├── data/
│   │   ├── loader.py       # CSV loading, timestamp normalisation, offer categorisation
│   │   ├── repositories.py # EventRepository abstraction
│   │   └── transforms.py   # Shared pandas transforms
│   ├── layout/
│   │   ├── root.py         # Root layout factory
│   │   ├── week_grid.py    # CSS grid builder for the weekly view
│   │   └── components/     # Header, modals, and store builders
│   ├── services/           # Layout helpers (timezone conversions, modal formatting)
│   └── visualization/      # Plotly chart generation for the day modal
├── logging/                # Logging configuration and rotation utilities
├── services/               # Config cache, colour resolution, parsing helpers
└── settings.py             # Environment and path helpers (loads .env when available)
```

Assets (Sass sources), data files, and automation scripts live alongside the package in their respective directories. See [docs/architecture/project_structure.md](../architecture/project_structure.md) for the full layout.

---

## 🧠 Recent Improvements

- **Theme persistence** – Theme preference now round-trips through a Dash store and client-side callback for instant updates.
- **Lookup cache warming** – `create_dash_app()` preloads JSON lookups (colours, keywords, hotel metadata) to remove first-click delays.
- **Data transforms** – `to_naive_utc` and `categorize_offer_types` normalise CSV input to predictable formats before rendering.
- **Logging upgrades** – HTTP access logging can be redirected to its own rotating file; maintenance scripts live under `scripts/python/`.

---

## 🚧 Work in Progress / Opportunities

- Improve accessibility (ARIA attributes on interactive controls, keyboard focus states).
- Expand automated tests for navigation and theming callbacks.
- Add CI workflow to exercise `npm run lint:css` (check) and `npm run lint:css:fix` alongside Python linters.
- Evaluate incremental data loading to reduce startup time on very large CSV files.

Track additional ideas in [guides/TODO.md](../guides/TODO.md).

---

## 🧪 Testing

- `pytest` – Core test suite
- `pytest tests/integration` – Dash integration tests (requires Chrome/Chromedriver)
- `scripts/shell/test.sh` – Convenience wrapper that runs formatters, linters, and pytest
- `python scripts/python/check_environment.py` – Verify Python/Node toolchain versions before running JS tooling

Enable the environment variable `CASINO_MINIMAL_TEST_LOG=1` to keep the main log noise-free during test runs.

---

## 🚀 Deployment

- Platform: [Render.com](https://render.com)
- Runtime: Python 3.11, Dash 3.x
- Command: `gunicorn app:server`
- Logs: Stored under `logs/` with rotation handled by `casino_calendar.logging.config`

---

## 🧼 Licence

Released under [The Unlicense](https://unlicense.org).
