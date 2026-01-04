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


def _looks_like_scan_bundle(input_dir: Path, text_files: list[Path]) -> bool:
    if not text_files:
        return False
    base_name = input_dir.name
    base_txt = f"{base_name}.txt"
    prefix = f"{base_name}."
    return all(path.name == base_txt or path.name.startswith(prefix) for path in text_files)


def _text_score(text: str) -> int:
    return sum(1 for char in text if char.isalnum())


def _select_best_text(
    input_dir: Path,
    text_files: list[Path],
) -> tuple[Path, str] | None:
    preferred_name = f"{input_dir.name}.txt"
    best_path: Path | None = None
    best_text = ""
    best_score = -1

    for text_path in text_files:
        text = text_path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            logger.warning("Skipping empty OCR text file: %s", text_path)
            continue
        if text_path.name == preferred_name:
            return text_path, text
        score = _text_score(text)
        if score > best_score:
            best_score = score
            best_path = text_path
            best_text = text

    if best_path is None:
        return None

    return best_path, best_text


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
        help="Directory to write prompt .txt files (default: scan inbox for subfolders).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing prompt files.",
    )
    return parser


def format_prompts(input_dir: Path, output_dir: Path | None, *, overwrite: bool) -> int:
    input_dir = Path(input_dir)
    if not input_dir.exists():
        logger.error("Input directory not found: %s", input_dir)
        return 1

    text_files = sorted(path for path in input_dir.iterdir() if path.is_file() and _is_ocr_text(path))
    if not text_files:
        logger.warning("No OCR .txt files found in %s", input_dir)
        return 0

    is_bundle = _looks_like_scan_bundle(input_dir, text_files)
    if output_dir is None:
        output_dir = input_dir.parent if is_bundle else input_dir
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if is_bundle:
        selection = _select_best_text(input_dir, text_files)
        if selection is None:
            logger.warning("No non-empty OCR .txt files found in %s", input_dir)
            return 0
        _, text = selection
        output_path = output_dir / f"{input_dir.name}.prompt.txt"
        if output_path.exists() and not overwrite:
            logger.info("Prompt already exists (use --overwrite to replace): %s", output_path)
            return 0
        prompt = build_event_extraction_prompt(text)
        output_path.write_text(prompt, encoding="utf-8")
        logger.info("Wrote prompt: %s", output_path)
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
    return format_prompts(args.input_dir, args.output_dir, overwrite=args.overwrite)


if __name__ == "__main__":
    raise SystemExit(main())
