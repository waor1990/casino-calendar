#!/usr/bin/env python3
"""Update CSS file to match SCSS spacing changes for event blocks."""

import re


def update_css_spacing():
    """Update the CSS file with spacing fixes."""
    css_file = (
        r"c:\Users\Wesley Allegre\source\repos\GitHub\Casino_Calendar\assets\style.css"
    )

    with open(css_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Fix .event-block-day margin
    content = re.sub(
        r"(\.event-block-day\s*\{[^}]*?)margin-left:\s*var\(--padding-xxs\);",
        r"\1margin: 0;",
        content,
        flags=re.DOTALL,
    )

    # Fix .event-block-day_text gap
    content = re.sub(
        r"(\.event-block-day_text\s*\{[^}]*?)gap:\s*var\(--padding-xxs\);",
        r"\1gap: 0;",
        content,
        flags=re.DOTALL,
    )

    # Fix .event-block-day_line margin-bottom
    content = re.sub(
        r"(\.event-block-day_line\s*\{[^}]*?)margin-bottom:\s*var\(--padding-xxs\);",
        r"\1margin: 0;",
        content,
        flags=re.DOTALL,
    )

    # Fix mobile media query margin
    mobile_section = re.search(
        r"(@media \(max-width: 480px\)[^}]*\.event-block-day\s*\{[^}]*?)margin-left:\s*var\(--padding-xxs\);",
        content,
        flags=re.DOTALL,
    )
    if mobile_section:
        content = re.sub(
            r"(@media \(max-width: 480px\)[^}]*\.event-block-day\s*\{[^}]*?)margin-left:\s*var\(--padding-xxs\);",
            r"\1margin: 0;",
            content,
            flags=re.DOTALL,
        )

    with open(css_file, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Updated CSS spacing rules:")
    print("  - Removed margin-left from .event-block-day")
    print("  - Removed gap from .event-block-day_text")
    print("  - Removed margin-bottom from .event-block-day_line")
    print("  - Fixed mobile media query margin")


if __name__ == "__main__":
    update_css_spacing()
