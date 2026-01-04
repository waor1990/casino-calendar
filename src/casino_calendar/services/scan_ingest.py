"""Scan inbox ingestion utilities for PDF-based casino event capture."""

from __future__ import annotations

import csv
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import fitz
import numpy as np
from PIL import Image, ImageFilter, ImageOps

from casino_calendar.dash_app.data.transforms import categorize_offer_type
from casino_calendar.logging.config import setup_logger
from casino_calendar.settings import DATA_DIR, get_env, get_env_int

logger = setup_logger(__name__)

DEFAULT_SCAN_INBOX = DATA_DIR / "raw" / "Casino_Scans"
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
    ocrmypdf_bin: str | None
    ocr_language: str
    ocr_dpi: int
    ocr_psm: int | None
    ocr_fallback_psm: int | None
    ocr_psm_sweep: list[int] | None
    ocr_preprocess: bool
    ocr_keep_preprocessed: bool
    text_layer_threshold: int
    save_source_texts: bool
    save_metadata: bool


@dataclass(frozen=True)
class AppendResult:
    rows_read: int
    rows_written: int
    rows_skipped: int
    json_payload: str


@dataclass(frozen=True)
class OcrSourceResult:
    name: str
    kind: str
    text: str
    score: int
    page_count: int | None


@dataclass(frozen=True)
class OcrBundle:
    sources: list[OcrSourceResult]
    best_source: str | None
    best_text: str
    text_layer_detected: bool


def load_scan_ingest_config() -> ScanIngestConfig:
    """Load scan ingest configuration from environment defaults."""

    inbox_dir = Path(get_env("SCAN_INBOX_DIR", str(DEFAULT_SCAN_INBOX)) or str(DEFAULT_SCAN_INBOX))
    ocr_output_dir = Path(get_env("SCAN_OCR_OUTPUT_DIR", str(DEFAULT_OCR_OUTPUT)) or str(DEFAULT_OCR_OUTPUT))
    csv_path = Path(get_env("CASINO_EVENTS_CSV", str(DEFAULT_CSV_PATH)) or str(DEFAULT_CSV_PATH))
    ghostscript_bin = get_env("GHOSTSCRIPT_BIN", "gs") or "gs"
    tesseract_bin = get_env("TESSERACT_BIN", "tesseract") or "tesseract"
    ocrmypdf_bin = _get_env_optional_text("OCRMYPDF_BIN", default="ocrmypdf")
    ocr_language = get_env("TESSERACT_LANG", "eng") or "eng"
    ocr_dpi = get_env_int("OCR_DPI", 300)
    ocr_psm = _get_env_optional_int("TESSERACT_PSM")
    ocr_fallback_psm = _get_env_optional_int("TESSERACT_FALLBACK_PSM", default=11)
    ocr_psm_sweep = _get_env_int_list("TESSERACT_PSM_SWEEP", default=[3, 6, 11])
    if ocr_psm_sweep == []:
        ocr_psm_sweep = None
    ocr_preprocess = _get_env_bool("SCAN_OCR_PREPROCESS", default=True)
    ocr_keep_preprocessed = _get_env_bool("SCAN_OCR_KEEP_PREPROCESSED", default=False)
    text_layer_threshold = get_env_int("OCR_TEXT_LAYER_THRESHOLD", 50)
    save_source_texts = _get_env_bool("SCAN_OCR_SAVE_SOURCES", default=False)
    save_metadata = _get_env_bool("SCAN_OCR_SAVE_METADATA", default=False)

    return ScanIngestConfig(
        inbox_dir=inbox_dir,
        ocr_output_dir=ocr_output_dir,
        csv_path=csv_path,
        ghostscript_bin=ghostscript_bin,
        tesseract_bin=tesseract_bin,
        ocrmypdf_bin=ocrmypdf_bin,
        ocr_language=ocr_language,
        ocr_dpi=ocr_dpi,
        ocr_psm=ocr_psm,
        ocr_fallback_psm=ocr_fallback_psm,
        ocr_psm_sweep=ocr_psm_sweep,
        ocr_preprocess=ocr_preprocess,
        ocr_keep_preprocessed=ocr_keep_preprocessed,
        text_layer_threshold=text_layer_threshold,
        save_source_texts=save_source_texts,
        save_metadata=save_metadata,
    )


def extract_text_from_pdf(pdf_path: Path, *, config: ScanIngestConfig) -> str:
    """Extract text from a PDF using text-layer extraction and OCR."""

    bundle = extract_text_bundle_from_pdf(pdf_path, config=config)
    return bundle.best_text


def extract_text_bundle_from_pdf(pdf_path: Path, *, config: ScanIngestConfig) -> OcrBundle:
    """Return OCR candidates and metadata for a PDF."""
    sources = list(_iter_text_candidates_from_pdf(pdf_path, config=config))
    best_text = ""
    best_score = -1
    best_source = None
    for source in sources:
        if source.score > best_score:
            best_text = source.text
            best_score = source.score
            best_source = source.name

    text_layer_detected = any(
        source.kind == "text_layer" and source.score >= config.text_layer_threshold for source in sources
    )

    return OcrBundle(
        sources=sources,
        best_source=best_source,
        best_text=best_text,
        text_layer_detected=text_layer_detected,
    )


def _iter_text_candidates_from_pdf(pdf_path: Path, *, config: ScanIngestConfig) -> Iterable[OcrSourceResult]:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Scanned PDF not found: {_format_log_path(pdf_path)}")

    page_count = _get_pdf_page_count(pdf_path)
    text_layer_detected = False

    pymupdf_text = _extract_text_with_pymupdf(pdf_path)
    if pymupdf_text:
        score = _text_score(pymupdf_text)
        yield OcrSourceResult(
            name="pymupdf",
            kind="text_layer",
            text=pymupdf_text,
            score=score,
            page_count=page_count,
        )
        if score >= config.text_layer_threshold:
            text_layer_detected = True

    native_text = _extract_text_layer(pdf_path, config=config)
    if native_text:
        score = _text_score(native_text)
        yield OcrSourceResult(
            name="ghostscript_txtwrite",
            kind="text_layer",
            text=native_text,
            score=score,
            page_count=page_count,
        )
        if score >= config.text_layer_threshold:
            text_layer_detected = True

    if text_layer_detected:
        return

    ocrmypdf_text = _extract_text_with_ocrmypdf(pdf_path, config=config)
    if ocrmypdf_text:
        yield OcrSourceResult(
            name="ocrmypdf",
            kind="ocr",
            text=ocrmypdf_text,
            score=_text_score(ocrmypdf_text),
            page_count=page_count,
        )

    ocr_text = _extract_text_with_tesseract(pdf_path, config=config)
    if ocr_text:
        text, ocr_page_count = ocr_text
        yield OcrSourceResult(
            name="ghostscript_tesseract",
            kind="ocr",
            text=text,
            score=_text_score(text),
            page_count=ocr_page_count or page_count,
        )


def _get_pdf_page_count(pdf_path: Path) -> int | None:
    try:
        with fitz.open(pdf_path) as doc:
            return doc.page_count
    except RuntimeError:
        return None


def _extract_text_with_pymupdf(pdf_path: Path) -> str | None:
    try:
        with fitz.open(pdf_path) as doc:
            page_texts = []
            for page in doc:
                text = page.get_text("text")
                if text:
                    text = text.strip()
                page_texts.append(text or "")
    except RuntimeError as exc:
        logger.warning("PyMuPDF failed to read %s: %s", _format_log_path(pdf_path), exc)
        return None

    combined = "\n".join(text for text in page_texts if text)
    combined = combined.strip()
    return combined or None


def _run_tesseract(image_path: Path, *, config: ScanIngestConfig, psm: int | None = None) -> str:
    command = [
        config.tesseract_bin,
        str(image_path),
        "stdout",
        "-l",
        config.ocr_language,
    ]
    if psm is not None:
        command.extend(["--psm", str(psm)])
    return _run_command(command)


def _preprocess_image(image_path: Path, output_dir: Path) -> Path | None:
    try:
        with Image.open(image_path) as image:
            image = image.convert("L")
            image = ImageOps.autocontrast(image)
            image = image.filter(ImageFilter.MedianFilter(size=3))
            gray = np.array(image)
            threshold = _otsu_threshold(gray)
            binary = (gray > threshold).astype(np.uint8) * 255
            processed = Image.fromarray(binary, mode="L")
            output_path = output_dir / f"{image_path.stem}-pre.png"
            processed.save(output_path, format="PNG")
            return output_path
    except (OSError, ValueError) as exc:
        logger.warning("Failed to preprocess %s: %s", _format_log_path(image_path), exc)
        return None


def _otsu_threshold(gray: np.ndarray) -> int:
    histogram, _ = np.histogram(gray.flatten(), bins=256, range=(0, 256))
    total = gray.size
    sum_total = int(np.dot(np.arange(256), histogram))
    sum_background = 0
    weight_background = 0
    max_between = -1.0
    threshold = 0
    for idx in range(256):
        weight_background += int(histogram[idx])
        if weight_background == 0:
            continue
        weight_foreground = total - weight_background
        if weight_foreground == 0:
            break
        sum_background += idx * int(histogram[idx])
        mean_background = sum_background / weight_background
        mean_foreground = (sum_total - sum_background) / weight_foreground
        between = weight_background * weight_foreground * (mean_background - mean_foreground) ** 2
        if between > max_between:
            max_between = between
            threshold = idx
    return threshold


def _extract_text_layer(pdf_path: Path, *, config: ScanIngestConfig) -> str | None:
    with tempfile.TemporaryDirectory(prefix="scan_ingest_txt_") as temp_dir:
        output_path = Path(temp_dir) / "native.txt"
        gs_command = [
            config.ghostscript_bin,
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=txtwrite",
            f"-sOutputFile={output_path}",
            str(pdf_path),
        ]
        logger.info("Running Ghostscript txtwrite for %s", _format_log_path(pdf_path))
        try:
            _run_command(gs_command)
        except OcrCommandError as exc:
            logger.warning("Ghostscript txtwrite failed for %s: %s", _format_log_path(pdf_path), exc)
            return None

        if not output_path.exists():
            return None
        text = output_path.read_text(encoding="utf-8", errors="ignore").strip()
        return text or None


def _extract_text_with_tesseract(pdf_path: Path, *, config: ScanIngestConfig) -> tuple[str, int] | None:
    output_dir = config.ocr_output_dir / pdf_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    output_pattern = str(output_dir / "page-%03d.png")
    gs_command = [
        config.ghostscript_bin,
        "-dSAFER",
        "-dBATCH",
        "-dNOPAUSE",
        "-sDEVICE=png16m",
        f"-r{config.ocr_dpi}",
        f"-sOutputFile={output_pattern}",
        str(pdf_path),
    ]

    logger.info("Running Ghostscript OCR render for %s", _format_log_path(pdf_path))
    _run_command(gs_command)

    image_paths = sorted(output_dir.glob("page-*.png"))
    if not image_paths:
        raise OcrCommandError(f"Ghostscript produced no images for {_format_log_path(pdf_path)}")

    preprocess_dir: Path | None = None
    preprocess_temp: tempfile.TemporaryDirectory[str] | None = None
    if config.ocr_preprocess:
        if config.ocr_keep_preprocessed:
            preprocess_dir = output_dir / "preprocessed"
            preprocess_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Saving preprocessed OCR images to %s", _format_log_path(preprocess_dir))
        else:
            preprocess_temp = tempfile.TemporaryDirectory(prefix="scan_ingest_pre_")
            preprocess_dir = Path(preprocess_temp.name)

    text_chunks: list[str] = []
    try:
        for image_path in image_paths:
            tesseract_image = image_path
            if config.ocr_preprocess and preprocess_dir is not None:
                processed = _preprocess_image(image_path, preprocess_dir)
                if processed is not None:
                    tesseract_image = processed

            if config.ocr_psm_sweep:
                psm_list = config.ocr_psm_sweep
                logger.info(
                    "Running Tesseract OCR sweep for %s with PSMs %s",
                    _format_log_path(image_path),
                    psm_list,
                )
                best_text = ""
                best_score = -1
                best_psm = None
                for psm in psm_list:
                    candidate = _run_tesseract(tesseract_image, config=config, psm=psm)
                    score = _text_score(candidate)
                    if score > best_score:
                        best_text = candidate
                        best_score = score
                        best_psm = psm
                if best_psm is not None:
                    logger.info(
                        "Using Tesseract OCR result for %s with PSM %s",
                        _format_log_path(image_path),
                        best_psm,
                    )
                text = best_text
            else:
                logger.info("Running Tesseract OCR for %s", _format_log_path(image_path))
                primary_text = _run_tesseract(tesseract_image, config=config, psm=config.ocr_psm)
                text = primary_text

                fallback_psm = config.ocr_fallback_psm
                if fallback_psm is not None and fallback_psm != config.ocr_psm:
                    logger.info(
                        "Running Tesseract OCR fallback for %s with PSM %s",
                        _format_log_path(image_path),
                        fallback_psm,
                    )
                    fallback_text = _run_tesseract(tesseract_image, config=config, psm=fallback_psm)
                    if _text_score(fallback_text) > _text_score(primary_text):
                        text = fallback_text
                        logger.info("Using fallback OCR result for %s", _format_log_path(image_path))

            text_chunks.append(text)
    finally:
        if preprocess_temp is not None:
            preprocess_temp.cleanup()

    combined = "\n".join(chunk.strip() for chunk in text_chunks if chunk.strip()).strip()
    if not combined:
        return None
    return combined, len(image_paths)


def _extract_text_with_ocrmypdf(pdf_path: Path, *, config: ScanIngestConfig) -> str | None:
    if not config.ocrmypdf_bin:
        return None

    with tempfile.TemporaryDirectory(prefix="scan_ingest_ocrmypdf_") as temp_dir:
        output_pdf = Path(temp_dir) / "output.pdf"
        sidecar = Path(temp_dir) / "sidecar.txt"
        command = [
            config.ocrmypdf_bin,
            "--force-ocr",
            "--deskew",
            "--clean",
            "--quiet",
            "--sidecar",
            str(sidecar),
            str(pdf_path),
            str(output_pdf),
        ]
        logger.info("Running OCRmyPDF for %s", _format_log_path(pdf_path))
        try:
            _run_command(command)
        except (OcrCommandError, FileNotFoundError) as exc:
            logger.warning("OCRmyPDF failed for %s: %s", _format_log_path(pdf_path), exc)
            return None

        if not sidecar.exists():
            return None
        text = sidecar.read_text(encoding="utf-8", errors="ignore").strip()
        return text or None


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

    bundle = extract_text_bundle_from_pdf(pdf_path, config=config)
    last_error: Exception | None = None
    for source in bundle.sources:
        try:
            events = parse_events_from_text(source.text)
        except ValueError as exc:
            logger.warning("OCR text from %s did not parse for %s: %s", source.name, _format_log_path(pdf_path), exc)
            last_error = exc
            continue

        logger.info("Using OCR text from %s for %s", source.name, _format_log_path(pdf_path))
        save_bundle = OcrBundle(
            sources=bundle.sources,
            best_source=source.name,
            best_text=source.text,
            text_layer_detected=bundle.text_layer_detected,
        )
        save_ocr_outputs(save_bundle, pdf_path=pdf_path, config=config)
        return append_events_to_csv(events, csv_path=config.csv_path)

    if bundle.best_text:
        logger.info(
            "Saving best OCR text from %s for %s despite parse failure",
            bundle.best_source,
            _format_log_path(pdf_path),
        )
        save_ocr_outputs(bundle, pdf_path=pdf_path, config=config)

    if last_error:
        raise last_error
    raise ValueError("OCR text is empty; no event blocks detected.")


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
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "(no stderr)"
        display_command = _format_command_for_log(command)
        raise OcrCommandError(f"Command failed ({result.returncode}): {display_command}\n{stderr}")
    return result.stdout or ""


def _get_env_optional_int(key: str, default: int | None = None) -> int | None:
    value = get_env(key)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_env_int_list(key: str, default: list[int] | None = None) -> list[int] | None:
    value = get_env(key)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"none", "off", "false", "0"}:
        return []
    values: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            values.append(int(part))
        except ValueError:
            continue
    return values or []


def _get_env_optional_text(key: str, default: str | None = None) -> str | None:
    value = get_env(key)
    if value is None:
        return default
    value = value.strip()
    return value or None


def _get_env_bool(key: str, default: bool = False) -> bool:
    value = get_env(key)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _text_score(text: str) -> int:
    return sum(1 for char in text if char.isalnum())


def _is_sparse_text(text: str, threshold: int = 10) -> bool:
    return _text_score(text) < threshold


def _resolve_scan_text_dir(pdf_path: Path, config: ScanIngestConfig) -> Path:
    output_root = Path(config.inbox_dir)
    return output_root / Path(pdf_path).stem


def save_ocr_text(
    ocr_text: str,
    *,
    pdf_path: Path,
    output_dir: Path | None = None,
) -> Path:
    """Persist OCR text for a scanned PDF."""

    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir) if output_dir is not None else pdf_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    ocr_path = output_dir / pdf_path.with_suffix(".txt").name
    ocr_path.write_text(ocr_text, encoding="utf-8")
    logger.info("Saved OCR text to %s", _format_log_path(ocr_path))
    return ocr_path


def save_ocr_outputs(
    bundle: OcrBundle,
    *,
    pdf_path: Path,
    config: ScanIngestConfig,
) -> dict[str, Path]:
    pdf_path = Path(pdf_path)
    output_dir = _resolve_scan_text_dir(pdf_path, config)
    output_dir.mkdir(parents=True, exist_ok=True)
    base_dir = output_dir.parent
    outputs: dict[str, Path] = {}
    source_paths: dict[str, Path] = {}

    outputs["best_text"] = save_ocr_text(bundle.best_text, pdf_path=pdf_path, output_dir=output_dir)

    if config.save_source_texts:
        for source in bundle.sources:
            source_path = output_dir / f"{pdf_path.stem}.{source.name}.txt"
            source_path.write_text(source.text, encoding="utf-8")
            source_paths[source.name] = source_path
            logger.info(
                "Saved OCR source text (%s) to %s",
                source.name,
                _format_log_path(source_path),
            )

    if config.save_metadata:
        metadata_path = output_dir / f"{pdf_path.stem}.ocr.json"
        source_payload = []
        for source in bundle.sources:
            entry = {
                "name": source.name,
                "kind": source.kind,
                "score": source.score,
                "page_count": source.page_count,
            }
            if source.name in source_paths:
                entry["text_path"] = _format_output_path(source_paths[source.name], base_dir)
            source_payload.append(entry)

        payload = {
            "pdf": _format_output_path(pdf_path, base_dir),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "text_layer_detected": bundle.text_layer_detected,
            "best_source": bundle.best_source,
            "best_text_path": _format_output_path(outputs["best_text"], base_dir),
            "sources": source_payload,
        }
        metadata_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        outputs["metadata"] = metadata_path
        logger.info("Saved OCR metadata to %s", _format_log_path(metadata_path))

    return outputs


def _format_log_path(path: Path) -> str:
    path = Path(path)
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return path.name


def _format_output_path(path: Path, base_dir: Path) -> str:
    path = Path(path)
    try:
        return str(path.relative_to(base_dir))
    except ValueError:
        return path.name


def _format_command_for_log(command: list[str]) -> str:
    parts: list[str] = []
    for part in command:
        if part.startswith("-sOutputFile="):
            prefix, value = part.split("=", 1)
            value_path = Path(value)
            if value_path.is_absolute():
                value = _format_log_path(value_path)
            parts.append(f"{prefix}={value}")
            continue

        try:
            candidate = Path(part)
        except (TypeError, ValueError):
            parts.append(part)
            continue

        if candidate.is_absolute() or candidate.exists():
            parts.append(_format_log_path(candidate))
        else:
            parts.append(part)
    return " ".join(parts)


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
