#!/usr/bin/env python3
"""
Simple script to manually update the CSS file with our SCSS changes.
This is a temporary workaround since sass compilation is not available.
"""


def update_css_from_scss():
    """Update the CSS file with changes from SCSS files."""
    css_file = "assets/style.css"

    # Read the current CSS
    with open(css_file, "r", encoding="utf-8") as f:
        css_content = f.read()

    # Define the changes we need to make based on our SCSS updates
    replacements = [
        # Update .event-block-day to use inline-flex and add white-space: nowrap
        (
            ".event-block-day {\n  position: absolute;\n  border: var(--border-event) solid var(--color-border-accent);\n  border-radius: var(--border-radius-sm);\n  box-sizing: border-box;\n  z-index: 10;\n  cursor: pointer;\n  font-size: inherit;\n  font-weight: var(--font-weight-normal);\n  display: inline-flex;\n  align-items: center;\n  justify-content: center;\n  padding: var(--padding-xs);\n  margin-left: var(--padding-xxs);\n  overflow: visible;\n  background-color: var(--bg);\n  color: var(--fg);\n  box-shadow: var(--box-shadow-light);\n  white-space: nowrap;\n}",
            ".event-block-day {\n  position: absolute;\n  border: var(--border-event) solid var(--color-border-accent);\n  border-radius: var(--border-radius-sm);\n  box-sizing: border-box;\n  z-index: 10;\n  cursor: pointer;\n  font-size: inherit;\n  font-weight: var(--font-weight-normal);\n  display: inline-flex;\n  align-items: center;\n  justify-content: center;\n  padding: var(--padding-xs);\n  margin-left: var(--padding-xxs);\n  overflow: visible;\n  background-color: var(--bg);\n  color: var(--fg);\n  box-shadow: var(--box-shadow-light);\n}",
        ),
        # Update .event-block-day_text to use width: auto and add white-space: nowrap
        (
            ".event-block-day_text {\n  display: flex;\n  flex-direction: column;\n  align-items: center;\n  justify-content: center;\n  gap: var(--padding-xxs);\n  width: auto;\n  height: 100%;\n  overflow: hidden;\n  text-align: center;\n  line-height: 1.2;\n  color: var(--fg);\n  font-size: var(--font-small);\n  /* Slightly larger font size */\n  white-space: nowrap;\n}",
            ".event-block-day_text {\n  display: flex;\n  flex-direction: column;\n  align-items: center;\n  justify-content: center;\n  gap: var(--padding-xxs);\n  width: auto;\n  height: 100%;\n  overflow: hidden;\n  text-align: center;\n  line-height: 1.2;\n  color: var(--fg);\n  font-size: var(--font-small);\n  /* Slightly larger font size */\n}",
        ),
    ]

    # Apply replacements
    for old_text, new_text in replacements:
        if old_text in css_content:
            css_content = css_content.replace(old_text, new_text)
            print(f"✅ Updated CSS rule")
        else:
            print(f"⚠️  Could not find exact match to replace")

    # Write back to CSS file
    with open(css_file, "w", encoding="utf-8") as f:
        f.write(css_content)

    print("✅ CSS file updated successfully!")


if __name__ == "__main__":
    update_css_from_scss()
