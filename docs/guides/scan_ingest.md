# Scanned PDF Ingestion

This guide describes the scan ingest pipeline that converts scanned PDFs into casino event rows for the app.

## Overview

The workflow mirrors the structure expected by `scripts/node/append-casino-event.mjs`:

1. Scanner software saves PDFs into a scan inbox directory.
2. Ghostscript renders PDF pages to images.
3. Tesseract OCR extracts text from each page.
4. The raw OCR text is saved next to the scanned PDF as a `.txt` file.
5. The OCR text is parsed into the required event fields.
6. `OfferType` is classified using the keyword rules used by the app.
7. Events are appended to `data/raw/casino_events.csv` with duplicate detection.

## Required OCR Fields

Each scanned PDF must include the following labels (one per line). The parser is case-insensitive and accepts
label variants like `Event`, `Start`, and `End`.

- `EventName`
- `Casino`
- `Location`
- `Offer`
- `StartDate`
- `EndDate`

Example OCR block:

```text
EventName: Weekly Slot Tournament
Casino: Example Casino
Location: 123 Main St, Example City, ST 12345
Offer: $10 free slot play
StartDate: 9/1/2025 9:00
EndDate: 9/1/2025 17:00
```

Each blank line separates events, so multiple events can be stacked in one scan. `OfferType` is computed from
`EventName` and `Offer` and does not need to appear in the scan.

## Configuration

The ingest pipeline uses environment variables for configuration:

- `SCAN_INBOX_DIR` (default: `data/raw/scan_inbox`)
- `SCAN_OCR_OUTPUT_DIR` (default: `data/cache/ocr`)
- `CASINO_EVENTS_CSV` (default: `data/raw/casino_events.csv`)
- `SCAN_INGEST_LOG_FILE` (default: `logs/scan_ingest.log` relative to the repo root)
- `GHOSTSCRIPT_BIN` (default: `gs`)
- `TESSERACT_BIN` (default: `tesseract`)
- `TESSERACT_LANG` (default: `eng`)
- `OCR_DPI` (default: `300`)

## Running the ingest

Process the newest scan in the inbox:

```bash
python scripts/python/scan_ingest.py
```

Process a specific file:

```bash
python scripts/python/scan_ingest.py --pdf path/to/scan.pdf
```

The CLI logs the JSON payload generated from OCR and the number of rows written or skipped.
The raw OCR text is saved alongside the PDF using the same filename with a `.txt` extension.
If the console window closes quickly, check `logs/scan_ingest.log` for the full run output (override with
`SCAN_INGEST_LOG_FILE` if you relocate the executable).
