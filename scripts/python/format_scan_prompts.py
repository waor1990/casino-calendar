"""Format OCR text files into prompt-ready instructions for event extraction."""

from __future__ import annotations

import argparse
from pathlib import Path

from casino_calendar.logging.config import setup_logger
from casino_calendar.services.scan_ingest import DEFAULT_SCAN_INBOX
from casino_calendar.services.scan_prompt import build_event_extraction_prompt

logger = setup_logger(__name__)


def _is_ocr_text(path: Path) -> bool:
    if path.suffix.lower() != ".txt":
        return False
    if path.name.endswith(".prompt.txt"):
        return False
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Format OCR .txt files into prompt-ready instructions for event extraction."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_SCAN_INBOX,
        help="Directory containing OCR .txt files (default: data/raw/Casino_Scans).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to write prompt .txt files (default: same as input).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing prompt files.",
    )
    return parser


def format_prompts(input_dir: Path, output_dir: Path, *, overwrite: bool) -> int:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    if not input_dir.exists():
        logger.error("Input directory not found: %s", input_dir)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    text_files = sorted(path for path in input_dir.iterdir() if path.is_file() and _is_ocr_text(path))
    if not text_files:
        logger.warning("No OCR .txt files found in %s", input_dir)
        return 0

    for text_path in text_files:
        text = text_path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            logger.warning("Skipping empty OCR text file: %s", text_path)
            continue

        output_path = output_dir / text_path.with_suffix(".prompt.txt").name
        if output_path.exists() and not overwrite:
            logger.info("Prompt already exists (use --overwrite to replace): %s", output_path)
            continue

        prompt = build_event_extraction_prompt(text)
        output_path.write_text(prompt, encoding="utf-8")
        logger.info("Wrote prompt: %s", output_path)

    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output_dir = args.output_dir or args.input_dir
    return format_prompts(args.input_dir, output_dir, overwrite=args.overwrite)


if __name__ == "__main__":
    raise SystemExit(main())
