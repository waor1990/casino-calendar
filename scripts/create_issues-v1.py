import os
import re

import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "waor1990/casino-calendar"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

# Load the markdown file
with open("docs/refactor_plan.md", "r", encoding="utf-8") as f:
    content = f.read()

categories = [
    "Architecture and Modular Design",
    "Callback and State Management",
    "Grid and Modal Rendering",
    "Styling and Responsiveness",
    "Data Handling and Time Normalization",
    "Testing Strategy",
    "Tooling and CI",
]

# Extract issues
issues = []
for category in categories:
    match = re.search(rf"## {re.escape(category)}\n\n((?:- .+\n)+)", content)
    if match:
        items = re.findall(r"- (.+)", match.group(1))
        for item in items:
            issues.append(
                {
                    "title": item[:80] + ("…" if len(item) > 80 else ""),
                    "body": f"**Category:** {category}\n\n{item}",
                    "labels": [category.lower().replace(" ", "-")],
                }
            )

# Create issues
for issue in issues:
    res = requests.post(
        f"https://api.github.com/repos/{REPO}/issues", json=issue, headers=HEADERS
    )
    if res.status_code == 201:
        url = res.json().get("html_url")
        # Note: Using print here since this is a one-off utility script
        # Production apps should use proper logging
        print(f"✅ Created: {url}")
    else:
        # Note: Using print here since this is a one-off utility script
        # Production apps should use proper logging
        print(f"❌ Failed: {issue['title']} ({res.status_code}) — {res.text}")
