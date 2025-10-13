"""Pytest configuration, fixtures, and logging hooks for Casino Calendar tests."""

from pathlib import Path
from typing import Optional

import os
import sys

import pytest

os.environ.setdefault('CASINO_MINIMAL_TEST_LOG', '1')

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from casino_calendar.logging import config as logging_config

MAINTENANCE_LOGGER = logging_config.setup_maintenance_logger("casino_calendar.tests.pytest")


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

    MAINTENANCE_LOGGER.info(
        "=== pytest session start: options=%s ===",
        session.config.invocation_params,
    )


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Log the end of a pytest session."""

    MAINTENANCE_LOGGER.info("=== pytest session finish: status=%s ===", exitstatus)


@pytest.hookimpl
def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Log individual test outcomes during the call phase."""

    if report.when != "call":
        return

    MAINTENANCE_LOGGER.info("Test %s -> %s", report.nodeid, report.outcome.upper())
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
    summary_body = ", ".join(parts) if parts else "no tests run"
    duration = getattr(terminalreporter._session, "duration", 0.0)
    MAINTENANCE_LOGGER.info("=== Summary: %s in %.2fs ===", summary_body, duration)
