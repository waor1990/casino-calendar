from __future__ import annotations

import importlib.util
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
for candidate in (SRC_DIR, PROJECT_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from casino_calendar.logging import app_logging  # noqa: E402
from casino_calendar.logging import config as logging_config  # noqa: E402

_PREFIX_RE = re.compile(r"^(?:\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{3})?|\d{2}:\d{2}:\d{2}) \| ")
_EMBEDDED_LOG_RE = re.compile(
    r"(?:\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{3})?|\d{2}:\d{2}:\d{2}) "
    r"\| (DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+\|"
)
_BANDIT_REPORT_PATH = PROJECT_ROOT / "logs" / "bandit_report.txt"
_PYDOCSTYLE_REPORT_PATH = PROJECT_ROOT / "logs" / "pydocstyle_report.txt"
_BANDIT_SEVERITY_RE = re.compile(r"^\s*Severity:\s+(\w+)\s+Confidence:\s+(\w+)\s*$")
_PYDOCSTYLE_CODE_RE = re.compile(r"\b(D\d{3})\b")
LINTING_CONFIG_DIR = PROJECT_ROOT / "config" / "linting"
BANDIT_CONFIG_PATH = LINTING_CONFIG_DIR / "bandit.yaml"
PYDOCSTYLE_CONFIG_PATH = LINTING_CONFIG_DIR / "pydocstyle.ini"
APP_CODE_DIR = SRC_DIR / "casino_calendar"
LINT_TARGETS = [str(APP_CODE_DIR), str(PROJECT_ROOT / "app.py"), str(PROJECT_ROOT / "wsgi.py")]


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

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if message == "":
            return ""
        if _PREFIX_RE.match(message):
            parts = message.split(" | ")
            if len(parts) >= 4:
                has_pid = parts[2].strip().startswith("pid=")
                location_index = 3 if has_pid else 2
                location = parts[location_index].strip() if location_index < len(parts) else parts[-2].strip()
                remainder = parts[-1].strip()
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


def run_step(logger: logging.Logger, step: Step, env: dict[str, str]) -> int:
    if step.available is not None and not step.available():
        logger.warning("%s not installed; skipping.", step.label)
        return 0

    logger.info("Step: %s", step.label)
    logger.debug("Running: %s", " ".join(step.command))

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
        with _BANDIT_REPORT_PATH.open("w", encoding="utf-8", newline="\n") as report_file:
            for line in process.stdout:
                line = line.rstrip("\r\n")
                report_file.write(f"{line}\n")
                if line.strip() == "Run metrics:":
                    saw_metrics = True
                match = _BANDIT_SEVERITY_RE.match(line)
                if match:
                    severity, confidence = match.groups()
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
                    total_issues += 1
            if not saw_metrics:
                report_file.write("\nSummary:\n")
                report_file.write(f"Total issues: {total_issues}\n")
                if severity_counts:
                    report_file.write("By severity:\n")
                    for key in sorted(severity_counts):
                        report_file.write(f"  {key}: {severity_counts[key]}\n")
                if confidence_counts:
                    report_file.write("By confidence:\n")
                    for key in sorted(confidence_counts):
                        report_file.write(f"  {key}: {confidence_counts[key]}\n")
    elif step.label == "pydocstyle":
        code_counts: dict[str, int] = {}
        total_issues = 0
        with _PYDOCSTYLE_REPORT_PATH.open("w", encoding="utf-8", newline="\n") as report_file:
            for line in process.stdout:
                line = line.rstrip("\r\n")
                report_file.write(f"{line}\n")
                match = _PYDOCSTYLE_CODE_RE.search(line)
                if match:
                    code = match.group(1)
                    code_counts[code] = code_counts.get(code, 0) + 1
                    total_issues += 1
            report_file.write("\nSummary:\n")
            report_file.write(f"Total issues: {total_issues}\n")
            if code_counts:
                report_file.write("By code:\n")
                for code in sorted(code_counts):
                    report_file.write(f"  {code}: {code_counts[code]}\n")
    else:
        suppressed = 0
        for line in process.stdout:
            line = line.rstrip("\r\n")
            if step.label == "black":
                line = line.encode("ascii", "ignore").decode("ascii")
                line = " ".join(line.split())
            if _EMBEDDED_LOG_RE.search(line):
                suppressed += 1
                continue
            logger.info(line)
        if suppressed:
            logger.debug("Suppressed %d embedded log line(s) during %s.", suppressed, step.label)

    code = process.wait()
    if step.label == "bandit":
        if code == 0:
            logger.info("Bandit report written to %s", _BANDIT_REPORT_PATH)
        else:
            logger.error("Bandit reported issues; see %s", _BANDIT_REPORT_PATH)
    elif step.label == "pydocstyle":
        if code == 0:
            logger.info("Pydocstyle report written to %s", _PYDOCSTYLE_REPORT_PATH)
        else:
            logger.warning("Pydocstyle reported issues; see %s", _PYDOCSTYLE_REPORT_PATH)
    return code


def prompt_fix(logger: logging.Logger, label: str) -> bool:
    if not sys.stdin.isatty():
        logger.warning("Non-interactive session; skipping %s fix prompt.", label)
        return False
    try:
        logger.info("%s reported formatting issues. Apply fixes now? [y/N]:", label)
        response = input().strip().lower()
    except EOFError:
        logger.warning("No response received; skipping %s fixes.", label)
        return False
    accepted = response in {"y", "yes"}
    logger.info("User response: %s", "yes" if accepted else "no")
    return accepted


def run_format_step(
    logger: logging.Logger,
    label: str,
    check_cmd: list[str],
    fix_cmd: list[str],
    env: dict[str, str],
    soft_failures: list[str],
) -> None:
    if not module_available(label):
        logger.warning("%s not installed; skipping.", label)
        return

    code = run_step(logger, Step(label, check_cmd), env)
    if code == 0:
        return

    logger.warning("%s reported formatting issues.", label)
    if prompt_fix(logger, label):
        fix_code = run_step(logger, Step(f"{label} (apply formatting)", fix_cmd), env)
        if fix_code == 0:
            return
        logger.error("%s formatting failed; review the output above.", label)
    else:
        logger.warning("%s formatting issues left unmodified.", label)

    soft_failures.append(label)


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
    logger.info("Log file: %s", logging_config.get_maintenance_log_path())
    logger.info("===============================================")
    logger.info("Python: %s", sys.executable)
    logger.info("Working directory: %s", PROJECT_ROOT)

    env = os.environ.copy()
    _BANDIT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PYDOCSTYLE_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    env.setdefault("PYTHONPATH", f"{PROJECT_ROOT / 'src'}{os.pathsep}{PROJECT_ROOT}")
    env.setdefault("PYTHONNOUSERSITE", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")

    soft_failures: list[str] = []

    compile_step = Step("Compile Python modules", [sys.executable, "-m", "compileall", "src"])
    code = run_step(logger, compile_step, env)
    if code != 0:
        logger.error("===============================================")
        logger.error("Tests failed. Review the output above.")
        logger.error("===============================================")
        return code

    run_format_step(
        logger,
        "black",
        [sys.executable, "-m", "black", "--check", "."],
        [sys.executable, "-m", "black", "."],
        env,
        soft_failures,
    )
    run_format_step(
        logger,
        "isort",
        [sys.executable, "-m", "isort", "--check-only", "."],
        [sys.executable, "-m", "isort", "."],
        env,
        soft_failures,
    )

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
            [sys.executable, "-m", "flake8", "--config", ".flake8", "."],
            available=lambda: module_available("flake8"),
        ),
        Step(
            "mypy",
            [sys.executable, "-m", "mypy", "--config-file", "config/typing/mypy.ini", "."],
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
        code = run_step(logger, step, env)
        if code != 0:
            if step.label == "bandit":
                soft_failures.append(step.label)
                continue
            if step.label == "pydocstyle":
                continue
            logger.error("===============================================")
            logger.error("Tests failed. Review the output above.")
            logger.error("===============================================")
            return code

    npm_path = shutil.which("npm") or shutil.which("npm.cmd") or shutil.which("npm.exe")
    if npm_path:
        code = run_step(logger, Step("Lint CSS", ["cmd", "/c", npm_path, "run", "lint:css"]), env)
        if code != 0:
            logger.error("===============================================")
            logger.error("Tests failed. Review the output above.")
            logger.error("===============================================")
            return code
    else:
        logger.warning("npm not found; skipping CSS lint.")

    code = run_step(
        logger,
        Step("Run pytest", [sys.executable, "-m", "pytest", "--cov=casino_calendar", "-vv", "-s", "tests"]),
        env,
    )
    if code != 0:
        logger.error("===============================================")
        logger.error("Tests failed. Review the output above.")
        logger.error("===============================================")
        return code

    if soft_failures:
        logger.warning("===============================================")
        logger.warning(
            "Tests completed with issues in: %s",
            ", ".join(soft_failures),
        )
        logger.warning("===============================================")
        return 1

    logger.info("===============================================")
    logger.info("Tests completed successfully.")
    logger.info("===============================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
