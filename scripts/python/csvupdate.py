"""CLI helper for normalising casino event CSV files.

Intended to be used from the ``csvupdate`` git alias so that newly added CSV
files are reshaped into the format expected by the Dash application.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"


def _ensure_project_on_path() -> None:
    """Ensure the repository root and src/ are importable for local execution."""
    sys.path[:0] = [str(SRC_DIR), str(PROJECT_ROOT)]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize a casino events CSV so that it matches the format "
            "expected by the app."
        )
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        help=(
            "Path to the CSV file to normalize. Defaults to the newest CSV "
            "detected via 'git status' or the canonical data/raw/casino_events.csv."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=(
            "Path for the normalized output. Defaults to in-place when the "
            "input is already data/raw/casino_events.csv, otherwise the "
            "canonical path."
        ),
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        dest="in_place",
        help="Overwrite the input file with the normalized output.",
    )
    parser.add_argument(
        "--no-sort",
        action="store_true",
        dest="no_sort",
        help="Do not reorder rows after normalization.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    _ensure_project_on_path()

    from casino_calendar.logging import config as logging_config
    from casino_calendar.services.csv_normalizer import (
        DEFAULT_OUTPUT_PATH,
        NormalizationResult,
        find_candidate_csv_paths,
        normalize_csv,
    )

    logger = logging_config.setup_maintenance_logger(
        "casino_calendar.scripts.csvupdate"
    )

    parser = build_parser()
    args = parser.parse_args(argv)

    input_path: Path | None = args.input
    if input_path is None:
        candidates = find_candidate_csv_paths()
        if len(candidates) == 1:
            input_path = candidates[0]
            logger.info("Detected CSV candidate via git status: %s", input_path)
        elif len(candidates) > 1:
            joined = ", ".join(str(path) for path in candidates)
            logger.error(
                "Multiple CSV candidates detected (%s). "
                "Use --input to specify the desired file.",
                joined,
            )
            return 2
        else:
            input_path = DEFAULT_OUTPUT_PATH
            logger.info("No new CSV detected; defaulting to %s", input_path)

    if not input_path.is_absolute():
        input_path = (Path.cwd() / input_path).resolve()

    canonical_output = (Path.cwd() / DEFAULT_OUTPUT_PATH).resolve()

    if args.output:
        output_path = args.output
    elif args.in_place or input_path == canonical_output:
        output_path = input_path
    else:
        output_path = canonical_output

    if not output_path.is_absolute():
        output_path = (Path.cwd() / output_path).resolve()

    try:
        result: NormalizationResult = normalize_csv(
            input_path=input_path,
            output_path=output_path,
            sort_rows=not args.no_sort,
        )
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return 1
    except ValueError as exc:
        logger.error(str(exc))
        return 1

    logger.info(
        "Wrote %d rows (%d read, %d skipped) to %s",
        result.rows_written,
        result.rows_read,
        result.skipped_rows,
        result.output_path,
    )

    for warning in result.warnings:
        logger.warning(warning)

    return 0


if __name__ == "__main__":
    sys.exit(main())
