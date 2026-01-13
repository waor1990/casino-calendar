"""Pytest configuration, fixtures, and logging hooks for Casino Calendar tests."""

from __future__ import annotations

import importlib
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from casino_calendar.bootstrap import bootstrap_environment  # noqa: E402

bootstrap_environment(PROJECT_ROOT)
os.environ.setdefault("CASINO_MINIMAL_TEST_LOG", "1")


class _PytestConsoleFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return getattr(record, "console", True)


class _PytestConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if record.levelno >= logging.WARNING and ("\n" in message or record.exc_info):
            return f"{record.levelname}: details logged to maintenance log"
        if record.exc_info:
            return f"{message}\n{self.formatException(record.exc_info)}"
        return message


def _setup_maintenance_logger():
    logging_config = importlib.import_module("casino_calendar.logging.config")
    logger = logging_config.setup_maintenance_logger("casino_calendar.tests.pytest")
    for handler in logger.handlers:
        if not isinstance(handler, logging.FileHandler):
            handler.addFilter(_PytestConsoleFilter())
            handler.setFormatter(_PytestConsoleFormatter())
    return logger


MAINTENANCE_LOGGER = _setup_maintenance_logger()


@pytest.fixture(autouse=True)
def _minimal_app_logging(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep production logs lean during test executions."""

    monkeypatch.setenv("CASINO_MINIMAL_TEST_LOG", "1")


@pytest.fixture
def casino() -> str:
    """Representative casino name used across tests."""

    return "Lucky Eagle Casino"


@pytest.fixture
def offer_type() -> str:
    """Representative offer type used across tests."""

    return "Giveaway"


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session: pytest.Session) -> None:
    """Log the start of a pytest session."""

    MAINTENANCE_LOGGER.info("Pytest session started.")


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Log the end of a pytest session."""

    try:
        exit_code = pytest.ExitCode(exitstatus)
        status_label = exit_code.name.replace("_", " ").lower()
    except ValueError:
        status_label = f"exit status {exitstatus}"

    MAINTENANCE_LOGGER.info("Pytest session finished with %s.", status_label)


@pytest.hookimpl
def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Log individual test outcomes during the call phase."""

    if report.when != "call":
        return

    if getattr(report, "wasxfail", False):
        outcome = "expected fail" if report.outcome == "failed" else "unexpected pass"
    else:
        outcome = report.outcome

    MAINTENANCE_LOGGER.info("Test %s %s.", report.nodeid, outcome, extra={"console": False})
    if report.failed:
        failure_details: Optional[str] = getattr(report, "longreprtext", None)
        if not failure_details and getattr(report, "longrepr", None):
            failure_details = str(report.longrepr)
        if failure_details:
            MAINTENANCE_LOGGER.error("Failure details:\n%s", failure_details)


@pytest.hookimpl
def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:  # type: ignore[override]
    """Record a concise summary similar to the terminal output."""

    stats = terminalreporter.stats
    ordered = ("failed", "error", "passed", "skipped", "xfailed", "xpassed")
    parts = []
    for outcome in ordered:
        items = stats.get(outcome, [])
        if items:
            label = "errors" if outcome == "error" else outcome
            parts.append(f"{len(items)} {label}")
    summary_body = ", ".join(parts) if parts else "no tests ran"
    duration = getattr(terminalreporter._session, "duration", 0.0)
    MAINTENANCE_LOGGER.info("Pytest summary: %s in %.2fs.", summary_body, duration)
