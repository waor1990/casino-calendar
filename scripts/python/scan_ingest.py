"""CLI helper for ingesting scanned PDF casino events."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
for candidate in (SRC_DIR, PROJECT_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from casino_calendar.logging.config import setup_logger  # noqa: E402
from casino_calendar.services.scan_ingest import (  # noqa: E402
    ingest_scan_pdf,
    list_scan_pdfs,
    load_scan_ingest_config,
)

logger = setup_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest scanned casino event PDFs with Ghostscript + Tesseract.")
    parser.add_argument(
        "--pdf",
        type=Path,
        help="Path to a scanned PDF to ingest. Defaults to the newest PDF in the scan inbox.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_scan_ingest_config()

    if args.pdf:
        pdf_path = args.pdf
    else:
        pdfs = list_scan_pdfs(config.inbox_dir)
        if not pdfs:
            logger.error("No scanned PDFs found in %s", config.inbox_dir)
            return 1
        pdf_path = pdfs[0]

    if not pdf_path.is_absolute():
        pdf_path = (Path.cwd() / pdf_path).resolve()

    try:
        result = ingest_scan_pdf(pdf_path, config=config)
    except Exception as exc:
        logger.error("Scan ingest failed: %s", exc)
        return 1

    logger.info(
        "Processed %s (read %d rows, wrote %d, skipped %d)",
        pdf_path,
        result.rows_read,
        result.rows_written,
        result.rows_skipped,
    )
    logger.info("JSON payload: %s", result.json_payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
