"""Scan inbox ingestion utilities for PDF-based casino event capture."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from casino_calendar.dash_app.data.transforms import categorize_offer_type
from casino_calendar.logging.config import setup_logger
from casino_calendar.settings import DATA_DIR, get_env, get_env_int

logger = setup_logger(__name__)

DEFAULT_SCAN_INBOX = DATA_DIR / "raw" / "scan_inbox"
DEFAULT_OCR_OUTPUT = DATA_DIR / "cache" / "ocr"
DEFAULT_CSV_PATH = DATA_DIR / "raw" / "casino_events.csv"
REQUIRED_FIELDS = ["EventName", "Casino", "Location", "Offer", "StartDate", "EndDate"]
CSV_HEADERS = [*REQUIRED_FIELDS, "OfferType"]

_FIELD_LABELS = {
    "eventname": "EventName",
    "event": "EventName",
    "casino": "Casino",
    "location": "Location",
    "offer": "Offer",
    "startdate": "StartDate",
    "start": "StartDate",
    "enddate": "EndDate",
    "end": "EndDate",
}


class OcrCommandError(RuntimeError):
    """Raised when OCR tooling returns a non-zero exit code."""


@dataclass(frozen=True)
class ScanIngestConfig:
    inbox_dir: Path
    ocr_output_dir: Path
    csv_path: Path
    ghostscript_bin: str
    tesseract_bin: str
    ocr_language: str
    ocr_dpi: int


@dataclass(frozen=True)
class AppendResult:
    rows_read: int
    rows_written: int
    rows_skipped: int
    json_payload: str


def load_scan_ingest_config() -> ScanIngestConfig:
    """Load scan ingest configuration from environment defaults."""

    inbox_dir = Path(get_env("SCAN_INBOX_DIR", str(DEFAULT_SCAN_INBOX)) or str(DEFAULT_SCAN_INBOX))
    ocr_output_dir = Path(get_env("SCAN_OCR_OUTPUT_DIR", str(DEFAULT_OCR_OUTPUT)) or str(DEFAULT_OCR_OUTPUT))
    csv_path = Path(get_env("CASINO_EVENTS_CSV", str(DEFAULT_CSV_PATH)) or str(DEFAULT_CSV_PATH))
    ghostscript_bin = get_env("GHOSTSCRIPT_BIN", "gs") or "gs"
    tesseract_bin = get_env("TESSERACT_BIN", "tesseract") or "tesseract"
    ocr_language = get_env("TESSERACT_LANG", "eng") or "eng"
    ocr_dpi = get_env_int("OCR_DPI", 300)

    return ScanIngestConfig(
        inbox_dir=inbox_dir,
        ocr_output_dir=ocr_output_dir,
        csv_path=csv_path,
        ghostscript_bin=ghostscript_bin,
        tesseract_bin=tesseract_bin,
        ocr_language=ocr_language,
        ocr_dpi=ocr_dpi,
    )


def extract_text_from_pdf(pdf_path: Path, *, config: ScanIngestConfig) -> str:
    """Extract OCR text from a PDF using Ghostscript + Tesseract."""

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Scanned PDF not found: {pdf_path}")

    output_dir = config.ocr_output_dir / pdf_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    output_pattern = str(output_dir / "page-%03d.png")
    gs_command = [
        config.ghostscript_bin,
        "-dSAFER",
        "-dBATCH",
        "-dNOPAUSE",
        "-sDEVICE=pngalpha",
        f"-r{config.ocr_dpi}",
        f"-sOutputFile={output_pattern}",
        str(pdf_path),
    ]

    logger.info("Running Ghostscript OCR render for %s", pdf_path)
    _run_command(gs_command)

    image_paths = sorted(output_dir.glob("page-*.png"))
    if not image_paths:
        raise OcrCommandError(f"Ghostscript produced no images for {pdf_path}")

    text_chunks: list[str] = []
    for image_path in image_paths:
        tesseract_command = [
            config.tesseract_bin,
            str(image_path),
            "stdout",
            "-l",
            config.ocr_language,
        ]
        logger.info("Running Tesseract OCR for %s", image_path)
        text_chunks.append(_run_command(tesseract_command))

    return "\n".join(chunk.strip() for chunk in text_chunks if chunk.strip())


def parse_events_from_text(text: str) -> list[list[str]]:
    """Parse OCR text into a JSON-style array of event rows."""

    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    if not blocks:
        raise ValueError("OCR text is empty; no event blocks detected.")

    events: list[list[str]] = []
    for block in blocks:
        fields: dict[str, str] = {}
        for line in block.splitlines():
            match = re.match(r"^\s*([A-Za-z ]+?)\s*:\s*(.+?)\s*$", line)
            if not match:
                continue
            label, value = match.groups()
            normalized = label.replace(" ", "").strip().lower()
            key = _FIELD_LABELS.get(normalized)
            if key:
                fields[key] = value.strip()

        missing = [field for field in REQUIRED_FIELDS if field not in fields]
        if missing:
            missing_fields = ", ".join(missing)
            raise ValueError(f"Missing required fields: {missing_fields}")

        events.append([fields[field] for field in REQUIRED_FIELDS])

    return events


def ingest_scan_pdf(pdf_path: Path, *, config: ScanIngestConfig) -> AppendResult:
    """Process a scanned PDF and append events to the CSV file."""

    ocr_text = extract_text_from_pdf(pdf_path, config=config)
    events = parse_events_from_text(ocr_text)
    return append_events_to_csv(events, csv_path=config.csv_path)


def list_scan_pdfs(inbox_dir: Path) -> list[Path]:
    """Return scanned PDFs from the inbox directory sorted by modified time."""

    inbox_dir = Path(inbox_dir)
    if not inbox_dir.exists():
        return []

    pdfs = [path for path in inbox_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdf"]
    return sorted(pdfs, key=lambda path: path.stat().st_mtime, reverse=True)


def append_events_to_csv(events: Iterable[Iterable[str]], *, csv_path: Path) -> AppendResult:
    """Append event rows to the CSV file, skipping duplicates."""

    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    events_list = [list(event) for event in events]
    payload_events = [*events_list]

    header, existing_rows = _load_csv_with_header(csv_path)
    header_index = {name: idx for idx, name in enumerate(header)}

    if "OfferType" in header_index:
        payload_events = [event + [categorize_offer_type(event[0], event[3])] for event in events_list]

    json_payload = json.dumps(payload_events, ensure_ascii=False)

    cleaned_existing = [_clean_row(row) for row in existing_rows]

    rows_written = 0
    rows_skipped = 0

    with csv_path.open("a", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        for event in events_list:
            if len(event) != len(REQUIRED_FIELDS):
                raise ValueError("Each event must have exactly six fields.")

            if _event_exists(event, cleaned_existing, header_index):
                rows_skipped += 1
                continue

            row = _build_csv_row(event, header, header_index)
            writer.writerow(row)
            rows_written += 1
            cleaned_existing.append(_clean_row(row))

    return AppendResult(
        rows_read=len(existing_rows),
        rows_written=rows_written,
        rows_skipped=rows_skipped,
        json_payload=json_payload,
    )


def _event_exists(
    event: list[str],
    existing_rows: list[list[str]],
    header_index: dict[str, int],
) -> bool:
    target = _clean_row(event)
    for row in existing_rows:
        if (
            row[header_index["Casino"]] == target[1]
            and row[header_index["StartDate"]] == target[4]
            and row[header_index["EndDate"]] == target[5]
        ):
            return True
    return False


def _clean_row(row: Iterable[str]) -> list[str]:
    return [str(value).strip().replace("\ufeff", "") for value in row]


def _run_command(command: list[str]) -> str:
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "(no stderr)"
        raise OcrCommandError(f"Command failed ({result.returncode}): {' '.join(command)}\n{stderr}")
    return result.stdout


def _load_csv_with_header(csv_path: Path) -> tuple[list[str], list[list[str]]]:
    if not csv_path.exists():
        with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(CSV_HEADERS)
        return CSV_HEADERS, []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        rows = list(reader)

    if not rows:
        with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(CSV_HEADERS)
        return CSV_HEADERS, []

    header = rows[0]
    existing_rows = rows[1:]

    if "OfferType" in header:
        return header, existing_rows

    missing_fields = [field for field in REQUIRED_FIELDS if field not in header]
    if missing_fields:
        raise ValueError(f"CSV header missing required fields: {', '.join(missing_fields)}")

    header_index = {name: idx for idx, name in enumerate(header)}
    updated_rows: list[list[str]] = []
    for row in existing_rows:
        event_name = row[header_index["EventName"]] if len(row) > header_index["EventName"] else ""
        offer = row[header_index["Offer"]] if len(row) > header_index["Offer"] else ""
        offer_type = categorize_offer_type(event_name, offer)
        updated_rows.append([*row, offer_type])

    new_header = [*header, "OfferType"]
    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(new_header)
        writer.writerows(updated_rows)

    return new_header, updated_rows


def _build_csv_row(event: list[str], header: list[str], header_index: dict[str, int]) -> list[str]:
    offer_type = categorize_offer_type(event[0], event[3])
    row = [""] * len(header)
    row[header_index["EventName"]] = event[0]
    row[header_index["Casino"]] = event[1]
    row[header_index["Location"]] = event[2]
    row[header_index["Offer"]] = event[3]
    row[header_index["StartDate"]] = event[4]
    row[header_index["EndDate"]] = event[5]
    if "OfferType" in header_index:
        row[header_index["OfferType"]] = offer_type
    return row
