import re
from pathlib import Path


def test_dark_theme_uses_primary_dark_instead_of_accent():
    variables = Path("assets/styles/_variables.scss").read_text(encoding="utf-8")
    dark_block = re.search(
        r'\[data-theme="dark"\][^{]*{([^}]*)}', variables, re.MULTILINE | re.DOTALL
    )
    assert dark_block, "dark theme block not found"
    assert "--color-accent" not in dark_block.group(1)

    scss_paths = [
        Path("assets/styles/_components.scss"),
        Path("assets/styles/_calendar_grid.scss"),
        Path("assets/styles/_modal.scss"),
    ]
    pattern = re.compile(
        r'\[data-theme="dark"\][^{]*{([^}]*)}', re.MULTILINE | re.DOTALL
    )
    found_primary = False
    for path in scss_paths:
        content = path.read_text(encoding="utf-8")
        for match in pattern.finditer(content):
            block = match.group(1)
            assert "var(--color-accent" not in block
            if "var(--color-primary-dark)" in block:
                found_primary = True
    assert found_primary, "no primary dark usage in dark theme blocks"
