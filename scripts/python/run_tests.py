from __future__ import annotations

import importlib.util
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, TextIO

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
for candidate in (SRC_DIR, PROJECT_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

os.environ.setdefault("CASINO_MINIMAL_TEST_LOG", "1")
os.environ.setdefault("LOG_FILE_TZ", "LOCAL")

from casino_calendar.logging import app_logging  # noqa: E402
from casino_calendar.logging import config as logging_config  # noqa: E402

_PREFIX_RE = re.compile(
    r"^(?:"
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z?"
    r"|\d{2}:\d{2}:\d{2}Z?"
    r"|\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{3})?"
    r"|[\w\.]+:[\w<>-]+:\d+"
    r") \| "
)
_EMBEDDED_LOG_RE = re.compile(
    r"(?:"
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z?"
    r"|\d{2}:\d{2}:\d{2}Z?"
    r"|\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{3})?"
    r") \| (DBG|INF|WRN|ERR|CRT)\s+\|"
    r"|[\w\.]+:[\w<>-]+:\d+ \|"
)
_PYTEST_STATUS_RE = re.compile(r"\b(PASSED|FAILED|SKIPPED|XPASS|XFAIL)\b")
_PYTEST_STATUS_ONLY_RE = re.compile(r"^(PASSED|FAILED|SKIPPED|XPASS|XFAIL)$")
_PYTEST_SUMMARY_START_RE = re.compile(r"^(PASSED|FAILED|SKIPPED|XPASS|XFAIL|ERROR)\b")
_BANDIT_SEVERITY_RE = re.compile(r"^\s*Severity:\s+(\w+)\s+Confidence:\s+(\w+)\s*$")
_PYDOCSTYLE_CODE_RE = re.compile(r"\b(D\d{3})\b")
LINTING_CONFIG_DIR = PROJECT_ROOT / "config" / "linting"
BANDIT_CONFIG_PATH = LINTING_CONFIG_DIR / "bandit.yaml"
PYDOCSTYLE_CONFIG_PATH = LINTING_CONFIG_DIR / "pydocstyle.ini"
APP_CODE_DIR = SRC_DIR / "casino_calendar"
LINT_TARGETS = [str(APP_CODE_DIR), str(PROJECT_ROOT / "app.py"), str(PROJECT_ROOT / "wsgi.py")]
TEST_REPORTS_DIR = PROJECT_ROOT / "logs" / "test_reports"
_QUIET_STEPS = {
    "pytest",
    "bandit",
    "pydocstyle",
    "flake8",
    "mypy",
    "lint css",
    "compile python modules",
    "black",
    "isort",
}
_STEP_LABEL_SANITIZER = re.compile(r"[^A-Za-z0-9-_]+")


def _sanitize_step_label(label: str) -> str:
    sanitized = _STEP_LABEL_SANITIZER.sub("_", label).strip("_")
    return sanitized or "step"


def _open_step_report(label: str, logger: logging.Logger) -> tuple[TextIO | None, Path | None]:
    try:
        TEST_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        file_name = f"{_sanitize_step_label(label)}_{timestamp}.txt"
        file_path = TEST_REPORTS_DIR / file_name
        writer = file_path.open("a", encoding="utf-8", newline="\n")
        return writer, file_path
    except OSError as exc:
        logger.warning("Failed to open step report for %s: %s", label, exc)
        return None, None


def _write_step_report_line(writer: TextIO | None, line: str) -> None:
    if not writer:
        return
    writer.write(line.rstrip("\r\n") + "\n")


def _display_path(path: Path, base: Path) -> str:
    try:
        rel = path.resolve().relative_to(base.resolve())
    except ValueError:
        return str(path)
    return "." if rel == Path(".") else str(rel)


class PrefixAwareFormatter(app_logging.FileFormatter):
    """Formatter that preserves already-formatted log lines."""

    def __init__(self) -> None:
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if message == "":
            return ""
        if _PREFIX_RE.match(message):
            return message
        return super().format(record)


class PrefixStrippingFormatter(app_logging.ConsoleFormatter):
    """Formatter that removes timestamps/levels for console output."""

    def __init__(self) -> None:
        super().__init__(use_colors=False, use_rich_markup=False)

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if message == "":
            return ""
        if _PREFIX_RE.match(message):
            parts = message.split(" | ")
            minimal_console = os.getenv("CASINO_MINIMAL_TEST_LOG", "").lower() not in (
                "",
                "0",
                "false",
                "off",
                "no",
            )
            if len(parts) >= 4:
                has_pid = parts[2].strip().startswith("pid=")
                location_index = 3 if has_pid else 2
                location = parts[location_index].strip() if location_index < len(parts) else parts[-2].strip()
                remainder = parts[-1].strip()
                if minimal_console:
                    return remainder or location
                if remainder:
                    return f"{location} | {remainder}"
                return location
            if len(parts) >= 2:
                location = parts[0].strip()
                remainder = " | ".join(parts[1:]).strip()
                if minimal_console:
                    return remainder or location
                if remainder:
                    return f"{location} | {remainder}"
                return location
        if record.exc_info:
            return f"{message}\n{self.formatException(record.exc_info)}"
        return super().format(record)


@dataclass(frozen=True)
class Step:
    label: str
    command: list[str]
    available: Callable[[], bool] | None = None


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def configure_logger() -> logging.Logger:
    logger = logging_config.setup_maintenance_logger("casino_calendar.scripts.run_tests")

    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.setFormatter(PrefixAwareFormatter())
        elif isinstance(handler, logging.StreamHandler):
            handler.setFormatter(PrefixStrippingFormatter())

    return logger


def _emit_process_line(
    logger: logging.Logger,
    step_key: str,
    line: str,
    suppressed: int,
) -> int:
    if step_key == "black":
        line = line.encode("ascii", "ignore").decode("ascii")
        line = " ".join(line.split())
    if _EMBEDDED_LOG_RE.search(line):
        return suppressed + 1
    if (
        "pytest" in step_key
        and line.startswith("Test ")
        and line.rstrip().endswith(
            (" passed.", " failed.", " skipped.", " xfailed.", " xpassed."),
        )
    ):
        return suppressed
    if step_key not in _QUIET_STEPS:
        logger.info(line)
    return suppressed


def _emit_pytest_line(
    logger: logging.Logger,
    line: str,
    suppressed: int,
    pending: str | None,
    last_emitted: str | None,
    seen_results: set[str],
    pending_coverage: str | None,
    pending_summary: str | None,
    quiet: bool = False,
) -> tuple[int, str | None, str | None, str | None, str | None]:
    raw_line = line.rstrip()
    stripped = raw_line.strip()
    if not stripped:
        if pending_summary:
            if pending_summary != last_emitted:
                if not quiet:
                    logger.info(pending_summary)
                last_emitted = pending_summary
            pending_summary = None
        return suppressed, pending, last_emitted, pending_coverage, pending_summary
    has_indent = raw_line.startswith((" ", "\t"))
    line = raw_line.lstrip()
    if pending_summary:
        if has_indent:
            pending_summary = f"{pending_summary} {line}"
            return suppressed, pending, last_emitted, pending_coverage, pending_summary
        if pending_summary != last_emitted:
            if not quiet:
                logger.info(pending_summary)
            last_emitted = pending_summary
        pending_summary = None
    if pending_coverage:
        if line == "Cover":
            line = f"{pending_coverage} Cover"
            pending_coverage = None
        else:
            if pending_coverage != last_emitted:
                if not quiet:
                    logger.info(pending_coverage)
                last_emitted = pending_coverage
            pending_coverage = None
    if _EMBEDDED_LOG_RE.search(line):
        return suppressed + 1, pending, last_emitted, pending_coverage, pending_summary
    if line.startswith("Test ") and line.rstrip().endswith(
        (" passed.", " failed.", " skipped.", " xfailed.", " xpassed."),
    ):
        return suppressed, pending, last_emitted, pending_coverage, pending_summary
    if pending:
        if line.startswith("tests/") and not _PYTEST_STATUS_RE.search(line):
            if pending != last_emitted:
                if not quiet:
                    logger.info(pending)
                last_emitted = pending
            pending = line
            return suppressed, pending, last_emitted, pending_coverage, pending_summary
        if _PYTEST_STATUS_ONLY_RE.match(line) or _PYTEST_STATUS_RE.search(line):
            line = f"{pending} {line}"
            pending = None
        else:
            if pending != last_emitted:
                if not quiet:
                    logger.info(pending)
                last_emitted = pending
            pending = None
    if "Pytest session finished" in line and not line.startswith("Pytest session finished"):
        prefix, suffix = line.split("Pytest session finished", 1)
        prefix = prefix.strip()
        if prefix and prefix != last_emitted:
            if not quiet:
                logger.info(prefix)
            last_emitted = prefix
        line = f"Pytest session finished{suffix}"
    if line.startswith("tests/") and not _PYTEST_STATUS_RE.search(line):
        return suppressed, line, last_emitted, pending_coverage, pending_summary
    if _PYTEST_STATUS_ONLY_RE.match(line):
        return suppressed, pending, last_emitted, pending_coverage, pending_summary
    if line.startswith("Name") and line.rstrip().endswith("Miss"):
        return suppressed, pending, last_emitted, line, pending_summary
    if line.startswith("tests/") and _PYTEST_STATUS_RE.search(line):
        if line in seen_results:
            return suppressed, pending, last_emitted, pending_coverage, pending_summary
        seen_results.add(line)
    if line == last_emitted:
        return suppressed, pending, last_emitted, pending_coverage, pending_summary
    if _PYTEST_SUMMARY_START_RE.match(line):
        pending_summary = line
        return suppressed, pending, last_emitted, pending_coverage, pending_summary
    if not quiet:
        logger.info(line)
    return suppressed, pending, line, pending_coverage, pending_summary


def run_step(logger: logging.Logger, step: Step, env: dict[str, str]) -> int:
    if step.available is not None and not step.available():
        logger.warning("%s not installed; skipping.", step.label)
        return 0

    logger.info("Step: %s", step.label)
    logger.debug("Running: %s", " ".join(step.command))
    step_report_writer, step_report_path = _open_step_report(step.label, logger)
    _write_step_report_line(step_report_writer, f"Step: {step.label}")

    try:
        try:
            process = subprocess.Popen(
                step.command,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
            )
        except FileNotFoundError:
            logger.exception("Failed to start %s (command not found).", step.label)
            return 1
        except Exception:
            logger.exception("Failed to start %s.", step.label)
            return 1

        assert process.stdout is not None
        if step.label == "bandit":
            severity_counts: dict[str, int] = {}
            confidence_counts: dict[str, int] = {}
            total_issues = 0
            saw_metrics = False
            for line in process.stdout:
                line = line.rstrip("\r\n")
                _write_step_report_line(step_report_writer, line)
                if line.strip() == "Run metrics:":
                    saw_metrics = True
                match = _BANDIT_SEVERITY_RE.match(line)
                if match:
                    severity, confidence = match.groups()
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
                    total_issues += 1
            if not saw_metrics:
                _write_step_report_line(step_report_writer, "")
                _write_step_report_line(step_report_writer, "Summary:")
                _write_step_report_line(step_report_writer, f"Total issues: {total_issues}")
                if severity_counts:
                    _write_step_report_line(step_report_writer, "By severity:")
                    for key in sorted(severity_counts):
                        _write_step_report_line(step_report_writer, f"  {key}: {severity_counts[key]}")
                if confidence_counts:
                    _write_step_report_line(step_report_writer, "By confidence:")
                    for key in sorted(confidence_counts):
                        _write_step_report_line(step_report_writer, f"  {key}: {confidence_counts[key]}")
        elif step.label == "pydocstyle":
            code_counts: dict[str, int] = {}
            total_issues = 0
            for line in process.stdout:
                line = line.rstrip("\r\n")
                _write_step_report_line(step_report_writer, line)
                match = _PYDOCSTYLE_CODE_RE.search(line)
                if match:
                    code = match.group(1)
                    code_counts[code] = code_counts.get(code, 0) + 1
                    total_issues += 1
            _write_step_report_line(step_report_writer, "")
            _write_step_report_line(step_report_writer, "Summary:")
            _write_step_report_line(step_report_writer, f"Total issues: {total_issues}")
            if code_counts:
                _write_step_report_line(step_report_writer, "By code:")
                for code in sorted(code_counts):
                    _write_step_report_line(step_report_writer, f"  {code}: {code_counts[code]}")
        else:
            suppressed = 0
            step_key = step.label.lower()
            pending_pytest: str | None = None
            last_emitted: str | None = None
            pending_coverage: str | None = None
            pending_summary: str | None = None
            seen_pytest_results: set[str] = set()
            for line in process.stdout:
                line = line.replace("\x00", "")
                if "\r" in line:
                    line = line.split("\r")[-1]
                line = line.rstrip("\n")
                stripped_line = line.strip()
                _write_step_report_line(step_report_writer, line)
                if "pytest" in step_key:
                    suppressed, pending_pytest, last_emitted, pending_coverage, pending_summary = _emit_pytest_line(
                        logger,
                        line,
                        suppressed,
                        pending_pytest,
                        last_emitted,
                        seen_pytest_results,
                        pending_coverage,
                        pending_summary,
                        quiet=True,
                    )
                else:
                    if not stripped_line:
                        continue
                    suppressed = _emit_process_line(logger, step_key, line, suppressed)
            if pending_pytest:
                if pending_pytest != last_emitted:
                    logger.info(pending_pytest)
                    last_emitted = pending_pytest
            if pending_summary and pending_summary != last_emitted:
                logger.info(pending_summary)
                last_emitted = pending_summary
            if pending_coverage and pending_coverage != last_emitted:
                logger.info(pending_coverage)
                last_emitted = pending_coverage
            if suppressed:
                logger.debug("Suppressed %d embedded log line(s) during %s.", suppressed, step.label)

        code = process.wait()
        _write_step_report_line(step_report_writer, f"{step.label} completed with exit code {code}.")
        logger.info("%s completed with exit code %d.", step.label, code)
        if step_report_path:
            logger.info("%s output recorded at %s", step.label, step_report_path)
        return code

    finally:
        if step_report_writer:
            step_report_writer.close()


def run_step_with_status(logger: logging.Logger, step: Step, env: dict[str, str]) -> str:
    if step.available is not None and not step.available():
        logger.warning("%s not installed; skipping.", step.label)
        return "skipped"
    code = run_step(logger, step, env)
    if code == 0:
        return "passed"
    return "failed"


def run_format_step(
    logger: logging.Logger,
    label: str,
    check_cmd: list[str],
    env: dict[str, str],
) -> str:
    if not module_available(label):
        logger.warning("%s not installed; skipping.", label)
        return "skipped"

    code = run_step(logger, Step(label, check_cmd), env)
    if code == 0:
        return "passed"

    logger.warning("%s reported formatting issues; skipping interactive fix prompt.", label)
    logger.warning("%s formatting issues left unmodified.", label)
    return "failed"


def record_step_status(
    label: str,
    status: str,
    passed_steps: list[str],
    failed_steps: list[str],
    skipped_steps: list[str],
) -> None:
    if status == "passed":
        passed_steps.append(label)
    elif status == "failed":
        failed_steps.append(label)
    elif status == "skipped":
        skipped_steps.append(label)


def rotate_old_reports(logger: logging.Logger) -> None:
    """Move reports older than today to dated subdirectories."""
    today = datetime.now().strftime("%Y%m%d")
    for file_path in TEST_REPORTS_DIR.glob("*.txt"):
        try:
            # Extract date from filename, e.g., Run_pytest_20260113-210149.txt -> 20260113
            parts = file_path.stem.split("_")
            if len(parts) >= 2 and len(parts[-1]) == 15 and parts[-1][8] == "-":
                date_str = parts[-1][:8]
                if date_str.isdigit() and date_str != today:
                    dated_dir = TEST_REPORTS_DIR / date_str
                    dated_dir.mkdir(exist_ok=True)
                    new_path = dated_dir / file_path.name
                    file_path.rename(new_path)
                    logger.debug("Rotated %s to %s", file_path.name, dated_dir)
        except (ValueError, OSError) as exc:
            logger.warning("Failed to rotate report %s: %s", file_path, exc)


def main() -> int:
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")

    logger = configure_logger()

    expected_venv = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    if not expected_venv.exists():
        logger.warning(".venv not found; using system Python instead.")

    logger.info("===============================================")
    logger.info("Casino Calendar - Test Runner")
    logger.info("Started test run.")
    maintenance_log = logging_config.get_maintenance_log_path()
    logger.info("Maintenance log: %s", _display_path(maintenance_log, PROJECT_ROOT))
    batch_log = os.getenv("CC_LOG_FILE")
    if batch_log:
        logger.info("Batch log: %s", _display_path(Path(batch_log), PROJECT_ROOT))
    logger.info("===============================================")
    python_display = _display_path(Path(sys.executable), PROJECT_ROOT)
    work_display = _display_path(PROJECT_ROOT, PROJECT_ROOT)
    logger.info("Python: %s", python_display)
    logger.info("Working directory: %s", work_display)

    env = os.environ.copy()
    env.setdefault("PYTHONPATH", f"{PROJECT_ROOT / 'src'}{os.pathsep}{PROJECT_ROOT}")
    env.setdefault("PYTHONNOUSERSITE", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("LOG_FILE_TZ", "LOCAL")
    env["COLUMNS"] = "240"

    passed_steps: list[str] = []
    failed_steps: list[str] = []
    skipped_steps: list[str] = []

    compile_step = Step("Compile Python modules", [sys.executable, "-m", "compileall", "src"])
    status = run_step_with_status(logger, compile_step, env)
    record_step_status(compile_step.label, status, passed_steps, failed_steps, skipped_steps)

    status = run_format_step(
        logger,
        "black",
        [sys.executable, "-m", "black", "--check", "--diff", "--verbose", "."],
        env,
    )
    record_step_status("black", status, passed_steps, failed_steps, skipped_steps)
    status = run_format_step(
        logger,
        "isort",
        [sys.executable, "-m", "isort", "--check-only", "--verbose", "."],
        env,
    )
    record_step_status("isort", status, passed_steps, failed_steps, skipped_steps)

    bandit_command = [
        sys.executable,
        "-m",
        "bandit",
        "-c",
        str(BANDIT_CONFIG_PATH),
        "-f",
        "txt",
        "-r",
        *LINT_TARGETS,
    ]
    pydocstyle_command = [
        sys.executable,
        "-m",
        "pydocstyle",
        "--config",
        str(PYDOCSTYLE_CONFIG_PATH),
        *LINT_TARGETS,
    ]

    steps = [
        Step(
            "flake8",
            [sys.executable, "-m", "flake8", "--config", ".flake8", "--verbose", "."],
            available=lambda: module_available("flake8"),
        ),
        Step(
            "mypy",
            [
                sys.executable,
                "-m",
                "mypy",
                "--config-file",
                "config/typing/mypy.ini",
                "--show-error-codes",
                "--error-summary",
                "--verbose",
                ".",
            ],
            available=lambda: module_available("mypy"),
        ),
        Step(
            "bandit",
            bandit_command,
            available=lambda: module_available("bandit"),
        ),
        Step("pydocstyle", pydocstyle_command, available=lambda: module_available("pydocstyle")),
    ]

    for step in steps:
        status = run_step_with_status(logger, step, env)
        record_step_status(step.label, status, passed_steps, failed_steps, skipped_steps)

    npm_path = shutil.which("npm") or shutil.which("npm.cmd") or shutil.which("npm.exe")
    if npm_path:
        status = run_step_with_status(logger, Step("Lint CSS", ["cmd", "/c", npm_path, "run", "lint:css"]), env)
    else:
        logger.warning("npm not found; skipping CSS lint.")
        status = "skipped"
    record_step_status("Lint CSS", status, passed_steps, failed_steps, skipped_steps)

    pytest_command = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=casino_calendar",
        "-vv",
        "-s",
        "--color=no",
        "-o",
        "console_output_style=classic",
        "tests",
    ]
    status = run_step_with_status(logger, Step("Run pytest", pytest_command), env)
    record_step_status("Run pytest", status, passed_steps, failed_steps, skipped_steps)

    logger.info("===============================================")
    if failed_steps:
        logger.error("Tests completed with failures.")
    else:
        logger.info("Tests completed successfully.")
    if passed_steps:
        logger.info("Passed: %s", ", ".join(passed_steps))
    if failed_steps:
        logger.error("Failed: %s", ", ".join(failed_steps))
    if skipped_steps:
        logger.warning("Skipped: %s", ", ".join(skipped_steps))
    logger.info("===============================================")
    rotate_old_reports(logger)
    if failed_steps:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
