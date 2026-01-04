"""Parse extracted OCR text files into structured casino event data."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from casino_calendar.logging.config import setup_logger
from casino_calendar.services.event_text_parser import parse_events_from_text
from casino_calendar.services.scan_ingest import append_events_to_csv, load_scan_ingest_config

logger = setup_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse OCR text files into casino event JSON or CSV rows.")
    parser.add_argument(
        "--input",
        type=Path,
        help="Path to a .txt file or directory containing OCR text files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/cache/parsed_events"),
        help="Directory to write per-file JSON outputs.",
    )
    parser.add_argument(
        "--append-csv",
        action="store_true",
        help="Append parsed events to the casino_events.csv file.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively search for .txt files when the input is a directory.",
    )
    return parser


def _collect_text_files(path: Path, *, recursive: bool) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() == ".txt" else []
    if not path.exists():
        return []
    iterator = path.rglob("*.txt") if recursive else path.glob("*.txt")
    return sorted([candidate for candidate in iterator if candidate.is_file()])


def _write_json(payload: list[dict[str, str]], *, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _group_text_files(text_files: list[Path]) -> dict[str, list[Path]]:
    grouped: dict[str, list[Path]] = {}
    for text_file in text_files:
        group_name = text_file.parent.name
        grouped.setdefault(group_name, []).append(text_file)
    return grouped


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_scan_ingest_config()

    input_path = args.input or config.inbox_dir
    text_files = _collect_text_files(input_path, recursive=args.recursive)
    if not text_files:
        logger.error("No .txt files found in %s", input_path)
        return 1

    grouped_files = _group_text_files(text_files)
    timestamp = datetime.now()
    for group_name, group_files in grouped_files.items():
        group_events = []
        for text_file in group_files:
            text = text_file.read_text(encoding="utf-8", errors="ignore")
            try:
                events = parse_events_from_text(text)
            except ValueError as exc:
                logger.warning("Skipping %s due to parse error: %s", text_file, exc)
                continue

            payload = [event.to_payload() for event in events]
            output_path = args.output_dir / group_name / f"{text_file.stem}.events.json"
            _write_json(payload, output_path=output_path)
            logger.info("Wrote %s", output_path)
            group_events.extend(events)

            if args.append_csv:
                rows = [event.to_row() for event in events if event.is_complete(allow_empty_offer=True)]
                if rows:
                    append_events_to_csv(rows, csv_path=config.csv_path)

        complete_payload = [event.to_payload() for event in group_events if event.is_complete(allow_empty_offer=True)]
        if complete_payload:
            combined_path = args.output_dir / group_name / f"parsed_events_{timestamp:%Y%m%d_%H%M%S}.json"
            _write_json(complete_payload, output_path=combined_path)
            logger.info("Wrote combined payload %s", combined_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
