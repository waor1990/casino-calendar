"""Prompt formatting for OCR-derived casino event text."""

from __future__ import annotations

from textwrap import dedent

PROMPT_TEMPLATE = dedent(
    """\
    You are an assistant designed to extract structured event information from casino promotional material.

    Instructions:

    - Extract all unique events from the text below.
    - Do not create separate entries for repeating time slots; use a single start and end time.
    - If an event occurs on a recurring weekday (e.g., “every Thursday in April”), return a separate event object for each occurrence.
    - If the flyer does not specify a time, default to:
      - StartDate = 00:00
      - EndDate = 23:59
    - Do not include dates or times in the Offer field.
    - Leave unknown fields as empty strings.

    Return the result as a JSON array of objects in exactly this schema:

    [
      {{
        "EventName": "",
        "Casino": "",
        "Location": "",
        "Offer": "",
        "StartDate": "",
        "EndDate": ""
      }}
    ]

    Dates must be in this format:
    "M/D/YYYY HH:mm" (24-hour time)

    Do not include explanations, markdown, or code fences.
    Return raw JSON only.

    Here is the promotional event text:
    \"\"\"
    {text}
    \"\"\"
    """
)


def build_event_extraction_prompt(text: str) -> str:
    """Format OCR text for event extraction prompts."""

    return PROMPT_TEMPLATE.format(text=text.strip())
