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

from casino_calendar.logging import config as logging_config  # noqa: E402

_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| ")


class PrefixAwareFormatter(logging_config.CasinoCalendarFormatter):
    """Formatter that preserves already-formatted log lines."""

    def __init__(self) -> None:
        super().__init__(use_colors=False)

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if message == "":
            return ""
        if _PREFIX_RE.match(message):
            return message
        return super().format(record)


class PrefixStrippingFormatter(logging.Formatter):
    """Formatter that removes timestamps/levels for console output."""

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if message == "":
            return ""
        if _PREFIX_RE.match(message):
            parts = message.split(" | ", 3)
            if len(parts) == 4:
                logger_name = parts[2].strip()
                remainder = parts[3]
                if remainder:
                    return f"{logger_name} | {remainder}"
                return logger_name
        if record.exc_info:
            return f"{message}\n{self.formatException(record.exc_info)}"
        return message


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
    for line in process.stdout:
        line = line.rstrip("\r\n")
        logger.info(line)

    return process.wait()


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
        Step("bandit", [sys.executable, "-m", "bandit", "-r", "."], available=lambda: module_available("bandit")),
        Step("pydocstyle", [sys.executable, "-m", "pydocstyle", "."], available=lambda: module_available("pydocstyle")),
    ]

    for step in steps:
        code = run_step(logger, step, env)
        if code != 0:
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
            "Tests completed with formatting issues in: %s",
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
