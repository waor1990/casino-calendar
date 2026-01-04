# Scanned PDF Ingestion

This guide describes the scan ingest pipeline that converts scanned PDFs into casino event rows for the app.

## Overview

The workflow mirrors the structure expected by `scripts/node/append-casino-event.mjs`:

1. Scanner software saves PDFs into a scan inbox directory.
2. PyMuPDF extracts any embedded text layer (for digital PDFs).
3. Ghostscript extracts any native text layer (txtwrite) when available.
4. If a text layer is detected, OCR is skipped to avoid degrading digital text.
5. OCRmyPDF runs for scanned PDFs when installed.
6. Ghostscript renders PDF pages to images.
7. Tesseract OCR preprocesses pages and runs a PSM sweep for higher-accuracy text.
8. The raw OCR text is saved under `<scan inbox>/<pdf-stem>/` as a `.txt` file.
9. The OCR text is parsed into the required event fields.
10. `OfferType` is classified using the keyword rules used by the app.
11. Events are appended to `data/raw/casino_events.csv` with duplicate detection.

Note: Text-layer extraction strips email header metadata (From/To/Reply-To lines, message counts, email addresses) before
scoring and saving `.txt` outputs.

Note: `scripts/python/scan_ingest.py` stops after step 8 and only saves OCR outputs under `<scan inbox>/<pdf-stem>/`.

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

- `SCAN_INBOX_DIR` (default: `data/raw/Casino_Scans`)
- `SCAN_OCR_OUTPUT_DIR` (default: `data/cache/ocr`)
- `CASINO_EVENTS_CSV` (default: `data/raw/casino_events.csv`)
- `SCAN_INGEST_LOG_FILE` (default: `logs/scan_ingest.log` relative to the repo root)
- `SCAN_INGEST_PAUSE_ON_EXIT` (default: `error`; set to `always` to keep the console open)
- `GHOSTSCRIPT_BIN` (default: `gs`)
- `TESSERACT_BIN` (default: `tesseract`)
- `TESSERACT_LANG` (default: `eng`)
- `TESSERACT_PSM` (optional: set a specific page segmentation mode)
- `TESSERACT_FALLBACK_PSM` (default: `11`; when set, OCR runs a second pass per page and keeps the richer output)
- `TESSERACT_PSM_SWEEP` (default: `3,6,11`; set to `none` to disable the sweep)
- `OCRMYPDF_BIN` (optional: path to `ocrmypdf`; set empty to disable)
- `OCR_DPI` (default: `300`)
- `SCAN_OCR_PREPROCESS` (default: `true`; applies grayscale + autocontrast + thresholding before OCR)
- `SCAN_OCR_KEEP_PREPROCESSED` (default: `false`; saves preprocessed OCR images under `data/cache/ocr/<pdf>/preprocessed`)
- `OCR_TEXT_LAYER_THRESHOLD` (default: `50`; minimum alphanumeric score to treat a PDF as text-based)
- `SCAN_OCR_SAVE_SOURCES` (default: `false`; when true, saves per-source `.txt` files)
- `SCAN_OCR_SAVE_METADATA` (default: `false`; when true, saves `.ocr.json` metadata)

When `TESSERACT_FALLBACK_PSM` is set and differs from `TESSERACT_PSM`, each page is OCR'd twice (primary + fallback),
and the result with more alphanumeric characters is used. To skip the fallback pass, set `TESSERACT_PSM` to the same
value as `TESSERACT_FALLBACK_PSM`.

## Running the ingest

Process the newest scan in the inbox:

```bash
python scripts/python/scan_ingest.py
```

Process a specific file:

```bash
python scripts/python/scan_ingest.py --pdf path/to/scan.pdf
```

You can also pass the PDF path as a positional argument (some scanner tools do this automatically):

```bash
python scripts/python/scan_ingest.py path/to/scan.pdf
```

The CLI logs the OCR extraction status and where the `.txt` output was saved.
The raw OCR text is saved under `<scan inbox>/<pdf-stem>/` as `<pdf-stem>.txt`, even if parsing fails.
When enabled via configuration, extra outputs are written to the same folder:

- `<pdf-stem>.ocr.json` metadata describing extraction sources and scores.
- `<pdf-stem>.<source>.txt` per-source text files (PyMuPDF, txtwrite, OCRmyPDF, Tesseract).
If the console window closes quickly, check `logs/scan_ingest.log` for the full run output (override with
`SCAN_INGEST_LOG_FILE` if you relocate the executable). A bootstrap line is written at startup to help
diagnose failures that occur before standard logging is configured.

## Parsing OCR text into event rows

Use `scripts/python/parse_event_texts.py` to turn the extracted `.txt` files into structured JSON payloads (and
optionally append them to `data/raw/casino_events.csv`).

```bash
python scripts/python/parse_event_texts.py --input data/raw/Casino_Scans --recursive
```

To append the parsed rows to the main CSV:

```bash
python scripts/python/parse_event_texts.py --input data/raw/Casino_Scans --recursive --append-csv
```

The parser applies the same field rules used by the manual AI prompt: one event per unique occurrence, default
times when missing (or invalid), recurring weekday expansion (for phrases like "every Thursday in April"), and
strips email-style headers (including header labels, email addresses, and nav bars) before parsing. Offer text is
scrubbed of date/time tokens (including weekdays) before output. Event blocks are anchored to date-bearing
sections, with undated lines folded into the nearest dated block. Wrapped sentence lines are merged before
selecting the event name to avoid partial-line titles. Per-file JSON outputs can include incomplete
fields; the combined `parsed_events_*.json` file requires EventName, Casino, Location, StartDate, and EndDate,
but allows empty Offer values. The parser uses
`data/lookups/casino_index.json` to detect the casino once per source file and applies the casino name and
location to every event it finds. Output JSON files are written to
`data/cache/parsed_events/<source-folder>/` by default, where `<source-folder>` matches the folder name under
`data/raw/Casino_Scans`.

## Rebuilding scan_ingest.exe

`scripts/python/scan_ingest.exe` is built with PyInstaller from `scripts/python/scan_ingest.py`. Rebuild it any time
you change scan ingest logic or dependencies.

From the repo root in the project virtual environment:

```bash
pip install pyinstaller
pyinstaller --onefile --name scan_ingest --distpath scripts/python --workpath build/scan_ingest --specpath build/scan_ingest scripts/python/scan_ingest.py
```

The executable will be written to `scripts/python/scan_ingest.exe`. Remove `build/scan_ingest` when you are done if
you do not need the build artifacts.
