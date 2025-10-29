import re
from pathlib import Path


def test_dark_theme_exposes_accent_token():
    variables = Path("assets/styles/partials/_variables.scss").read_text(
        encoding="utf-8"
    )
    dark_block = re.search(
        r'\[data-theme="dark"\][^{]*{([^}]*)}', variables, re.MULTILINE | re.DOTALL
    )
    assert dark_block, "dark theme block not found"
    dark_content = dark_block.group(1)
    assert "--color-accent" in dark_content
    assert "--color-accent-rgb" in dark_content
    assert "#7dd3fc" not in dark_content.lower()
    assert "125 211 252" not in dark_content

    scss_paths = [
        Path("assets/styles/partials/_components.scss"),
        Path("assets/styles/partials/_calendar_grid.scss"),
        Path("assets/styles/partials/_modal.scss"),
    ]
    pattern = re.compile(
        r'\[data-theme="dark"\][^{]*{([^}]*)}', re.MULTILINE | re.DOTALL
    )
    found_accent_usage = False
    for path in scss_paths:
        content = path.read_text(encoding="utf-8")
        for match in pattern.finditer(content):
            block = match.group(1)
            if "var(--color-accent" in block:
                found_accent_usage = True
    assert found_accent_usage, "dark theme blocks should use accent token"


def test_event_detail_span_uses_bg_color():
    content = Path("assets/styles/partials/_components.scss").read_text(
        encoding="utf-8"
    )
    pattern = re.compile(r"\.event-label span\s*{[^}]*color:\s*var\(--bg\)")
    assert pattern.search(content), "event detail span should use --bg color"
