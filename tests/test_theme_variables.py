import re
from pathlib import Path


def test_dark_theme_accent_uses_primary_dark():
    content = Path("assets/styles/_variables.scss").read_text(encoding="utf-8")
    dark_block = re.search(
        r'\[data-theme="dark"\]\s*\{([^}]*)\}', content, re.MULTILINE | re.DOTALL
    )
    assert dark_block, "dark theme block not found"
    block_text = dark_block.group(1)
    accent = re.search(r"--color-accent:\s*(.*?);", block_text)
    accent_dark = re.search(r"--color-accent-dark:\s*(.*?);", block_text)
    assert accent and accent_dark, "accent variables not found"
    assert accent.group(1).strip() == "var(--color-primary-dark)"
    assert accent_dark.group(1).strip() == "var(--color-primary-dark)"
