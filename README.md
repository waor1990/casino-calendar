# 🎰 Casino Event Calendar

A personal-use Dash app that visualizes casino events on a rolling 4-week calendar. Built with Plotly, Dash, and Python.

---

## 🚀 Features

- Navigate up to ±6 weeks from today
- Toggle weekly blocks and ongoing events
- Clickable events show detailed modal popup
- Responsive UI for phones, tablets, and desktop
- Time zone localized to Pacific Time (PDT)
- Modular code structure for maintainability

---

## 🧱 Project Structure

.
├── app.py # Dash entry point
├── calendar/ # Modular app logic
│ ├── callbacks.py # All Dash callbacks
│ ├── data.py # CSV loader with timezone handling
│ ├── layout.py # Layout + legend/header generation
│ ├── plotting.py # Chart logic
│ ├── utils.py # Responsive settings, date logic
│ └── init.py
├── assets/
│ └── modal.css # Custom modal styling
├── casino_events.csv # Event data
├── requirements.txt
├── Procfile # For Render deployment
└── README.md


---

## 🛠️ Running Locally

```bash
pip install -r requirements.txt
python app.py

🌐 Deploying to Render
Your Procfile should contain:

procfile
Copy
Edit
web: gunicorn app:server
Push this repo to GitHub and connect it to a Render Web Service.

🧼 License
MIT — personal use, modify freely.

sql
Copy
Edit
