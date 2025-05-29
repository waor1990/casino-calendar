# 🎰 Casino Calendar App — Developer Handoff

## 📌 Overview

This is a responsive, interactive web application built using **Dash (Plotly)** and deployed on **Render.com**. It visualizes casino events in a calendar-style layout with weekly and daily modal views.

---

## ✅ Current Features

- 📆 **Weekly View** with events displayed as blocks on a timeline.
- 🔍 **Modal Details** for individual events or entire day views.
- 📱 **Responsive Design** using screen width and height.
- 🖼️ **Dynamic CSS Styling** via a centralized `custom.css` with variables and utility classes.
- 🎨 **Legend** auto-generated from the dataset.

---

## 📁 Project Structure Highlights

casino_calendar/
│
├── app_components/
│ ├── layout.py # App layout (header, modals, containers)
│ ├── callbacks.py # Dash callbacks
│ ├── data.py # Loads and processes event data
│ ├── plotting.py # Chart rendering logic (weekly & daily)
│ ├── utils.py # Responsive sizing, helpers, constants
│
├── assets/
│ └── custom.css # Centralized styling with CSS variables
│
├── app.py # Dash entry point (if used)
└── requirements.txt # Dependencies

---

## 🧠 Recent Refactors

### ✅ Screen Responsiveness

- Screen dimensions are now determined **client-side** using `window.innerWidth` and `innerHeight`.
- This eliminates static screen width references in Python.

### ✅ Custom CSS Overhaul

- Uses `:root` CSS variables for:
  - Padding/margin
  - Font sizes
  - Layout gaps
- Utility classes applied via `className` in layout components.

### ✅ Rewritten Functions

- `render_single_week_chart()` and `render_sticky_header()` are fully dynamic and use computed values from CSS logic.
- `generate_day_view_html()` pulls layout sizes from a helper.

---

## 🛠️ Work in Progress / To-Do

### 🔧 Modularize CSS

Break `custom.css` into:

- `base.css`: Root variables and resets
- `typography.css`: Fonts and titles
- `layout.css`: General spacing/layout
- `components.css`: Buttons, modals
- `animations.css`: Fade/slide effects

_All `.css` files in `/assets/` are automatically included by Dash._

### 📱 Fine-Tune Responsiveness

- Review behavior on mobile/tablet.
- Adjust padding/margins dynamically where needed.

### ✨ Optional Enhancements

- Add TailwindCSS or SCSS preprocessor for better styling workflow.
- Improve accessibility (keyboard nav, ARIA tags).
- Animate modal transitions with CSS only.

---

## 🚨 Known Issues (Fixed)

- `TypeError` in `render_single_week_chart()` and `render_sticky_header()` due to incorrect argument count. ✅ Fixed.
- Double use of `sticky_header()` has been harmonized. ✅

---

## 📦 Deployment Info

- Hosted on: [Render.com](https://render.com/)
- **Live App**: [https://casino-calendar.onrender.com](https://casino-calendar.onrender.com)
- Environment: Python 3.11, Dash (latest), Flask (via Dash)
- Auto-build triggered on commits.

---

## 🧰 Helper Functions of Note

```python
# utils.py

def get_layout_config(screen_width):
    # Returns font_sizes, padding_sizes, hour_height, label_column_pct
    ...
```python
