"""CLI helper for ingesting scanned PDF casino events."""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


def resolve_project_root() -> Path:
    if getattr(sys, "frozen", False):
        exe_path = Path(sys.executable).resolve()
        candidate = exe_path.parents[2] if len(exe_path.parents) > 2 else exe_path.parent
        if (candidate / "src" / "casino_calendar").exists():
            return candidate
        return Path.cwd()
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = resolve_project_root()
SRC_DIR = PROJECT_ROOT / "src"
for candidate in (SRC_DIR, PROJECT_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)

DEFAULT_LOG_PATH = PROJECT_ROOT / "logs" / "scan_ingest.log"


def resolve_log_path(project_root: Path) -> Path:
    override = os.getenv("SCAN_INGEST_LOG_FILE")
    if override:
        path = Path(override)
        return (project_root / path).resolve() if not path.is_absolute() else path
    return DEFAULT_LOG_PATH


LOG_FILE_PATH = resolve_log_path(PROJECT_ROOT)
os.environ["LOG_FILE"] = str(LOG_FILE_PATH)


def _write_bootstrap_log(message: str, exc: BaseException | None = None) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"{timestamp} | BOOTSTRAP | {message}"]
    if exc is not None:
        stack = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        lines.append(stack.rstrip())
    try:
        LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write("\n".join(lines) + "\n")
    except Exception:
        pass


_write_bootstrap_log("scan ingest bootstrap starting")


def _should_pause_on_exit(exit_code: int | None) -> bool:
    if not getattr(sys, "frozen", False):
        return False
    mode = os.getenv("SCAN_INGEST_PAUSE_ON_EXIT", "error").lower()
    if mode in {"0", "false", "no", "off", "never"}:
        return False
    if mode in {"1", "true", "yes", "on", "always"}:
        return True
    return exit_code not in (0, None)


def _pause_for_console() -> None:
    try:
        input("Press Enter to close...")
    except (EOFError, KeyboardInterrupt):
        pass


from casino_calendar.logging.config import setup_logger  # noqa: E402
from casino_calendar.services.scan_ingest import (  # noqa: E402
    extract_text_bundle_from_pdf,
    list_scan_pdfs,
    load_scan_ingest_config,
    save_ocr_outputs,
)

logger = setup_logger(__name__, log_file=os.environ.get("LOG_FILE"))


PLACEHOLDER_PDF_ARGS = {"%1", "%~1"}


def normalize_pdf_argument(pdf_arg: Path | None) -> Path | None:
    if pdf_arg is None:
        return None
    raw = str(pdf_arg).strip()
    if raw in PLACEHOLDER_PDF_ARGS:
        logger.warning("PDF argument placeholder %s detected; using scan inbox instead", raw)
        return None
    return pdf_arg


def _format_log_path(path: Path) -> str:
    path = Path(path)
    for base in (PROJECT_ROOT, Path.cwd()):
        try:
            return str(path.relative_to(base))
        except ValueError:
            continue
    return path.name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract text from scanned casino PDFs with text-layer and OCR.")
    parser.add_argument(
        "--pdf",
        type=Path,
        help="Path to a scanned PDF to ingest. Defaults to the newest PDF in the scan inbox.",
    )
    parser.add_argument(
        "pdf_path",
        nargs="?",
        type=Path,
        help="Path to a scanned PDF (positional). Useful when a scanner passes the file path directly.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_scan_ingest_config()
    logger.info("Scan ingest starting (log file: %s)", os.environ.get("LOG_FILE"))
    logger.info("Using Ghostscript bin: %s", config.ghostscript_bin)
    logger.info("Using Tesseract bin: %s", config.tesseract_bin)
    logger.info("Using Tesseract PSM: %s", config.ocr_psm)
    logger.info("Using Tesseract fallback PSM: %s", config.ocr_fallback_psm)
    logger.info("Using Tesseract PSM sweep: %s", config.ocr_psm_sweep)
    logger.info("OCR preprocessing enabled: %s", config.ocr_preprocess)

    pdf_arg = normalize_pdf_argument(args.pdf) or normalize_pdf_argument(args.pdf_path)
    if pdf_arg:
        pdf_path = pdf_arg
    else:
        pdfs = list_scan_pdfs(config.inbox_dir)
        if not pdfs:
            logger.error("No scanned PDFs found in %s", _format_log_path(config.inbox_dir))
            return 1
        pdf_path = pdfs[0]

    if not pdf_path.is_absolute():
        pdf_path = (Path.cwd() / pdf_path).resolve()

    try:
        bundle = extract_text_bundle_from_pdf(pdf_path, config=config)
        save_ocr_outputs(bundle, pdf_path=pdf_path, config=config)
    except Exception as exc:
        logger.exception("Scan ingest failed: %s", exc)
        return 1

    logger.info("Extracted OCR text for %s", _format_log_path(pdf_path))
    return 0


if __name__ == "__main__":
    exit_code: int | None = 0
    try:
        exit_code = main()
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 1
        if _should_pause_on_exit(exit_code):
            _pause_for_console()
        raise
    except Exception as exc:
        _write_bootstrap_log("scan ingest crashed before logging initialized", exc)
        exit_code = 1
        if _should_pause_on_exit(exit_code):
            _pause_for_console()
        raise
    if _should_pause_on_exit(exit_code):
        _pause_for_console()
    raise SystemExit(exit_code)
