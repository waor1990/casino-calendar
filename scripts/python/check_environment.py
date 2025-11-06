from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
for candidate in (SRC_DIR, PROJECT_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

try:
    from casino_calendar.logging import config as logging_config  # noqa: E402
except Exception as exc:  # pragma: no cover - fallback path
    logging.basicConfig(
        level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger = logging.getLogger("casino_calendar.scripts.check_environment")
    logger.warning(
        "Falling back to basic logging because casino_calendar logging config "
        "could not be imported: %s",
        exc,
    )
else:
    logger = logging_config.setup_maintenance_logger(
        "casino_calendar.scripts.check_environment"
    )

PYTHON_MIN_VERSION = (3, 11, 0)


@dataclass
class CheckFailure:
    component: str
    requirement: str
    detected: str
    guidance: str


def parse_semver(version: str) -> tuple[int, int, int]:
    """Parse a semantic version into a comparable tuple."""

    cleaned = version.strip()
    if cleaned.startswith("v"):
        cleaned = cleaned[1:]
    cleaned = cleaned.split("-", 1)[0]
    cleaned = cleaned.split("+", 1)[0]

    parts = [int(part) for part in cleaned.split(".") if part]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])  # type: ignore[return-value]


def format_semver(version: Iterable[int]) -> str:
    parts = list(version)
    if len(parts) >= 3:
        return f"{parts[0]}.{parts[1]}.{parts[2]}"
    if len(parts) == 2:
        return f"{parts[0]}.{parts[1]}"
    return str(parts[0]) if parts else "unknown"


def satisfies_spec(version: tuple[int, int, int], spec: str) -> bool:
    """Validate version against a limited subset of npm semver ranges."""

    spec = spec.strip()
    if not spec:
        return True

    if "||" in spec:
        return any(satisfies_spec(version, part) for part in spec.split("||"))
    if " " in spec:
        return all(satisfies_spec(version, part) for part in spec.split())

    if spec.startswith("^"):
        base = parse_semver(spec[1:])
        return version[0] == base[0] and version >= base
    if spec.startswith("~"):
        base = parse_semver(spec[1:])
        return version[0] == base[0] and version[1] == base[1] and version >= base
    if spec.startswith(">="):
        base = parse_semver(spec[2:])
        return version >= base
    if spec.startswith(">"):
        base = parse_semver(spec[1:])
        return version > base
    if spec.startswith("<="):
        base = parse_semver(spec[2:])
        return version <= base
    if spec.startswith("<"):
        base = parse_semver(spec[1:])
        return version < base

    exact = parse_semver(spec)
    return version == exact


def run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def load_package_metadata() -> dict:
    pkg_path = PROJECT_ROOT / "package.json"
    data = json.loads(pkg_path.read_text(encoding="utf-8"))
    return data


def detect_python_version() -> tuple[int, int, int]:
    info = sys.version_info
    return info.major, info.minor, info.micro


def detect_node_version() -> tuple[int, int, int] | None:
    node = shutil.which("node")
    if node is None:
        return None
    result = run_command([node, "--version"])
    if result.returncode != 0:
        logger.debug("node --version stderr: %s", result.stderr.strip())
        return None
    return parse_semver(result.stdout.strip())


def detect_npm_version() -> tuple[int, int, int] | None:
    npm = shutil.which("npm")
    if npm is None:
        return None
    result = run_command([npm, "--version"])
    if result.returncode != 0:
        logger.debug("npm --version stderr: %s", result.stderr.strip())
        return None
    return parse_semver(result.stdout.strip())


def prompt_yes_no(message: str, default: bool, interactive: bool) -> bool:
    if not interactive:
        return default
    prompt = " [Y/n] " if default else " [y/N] "
    while True:
        try:
            response = input(message + prompt).strip().lower()
        except EOFError:
            return default
        if not response:
            return default
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("Please respond with 'y' or 'n'.")


def desired_node_version(pkg_data: dict) -> str | None:
    volta_cfg = pkg_data.get("volta", {})
    volta_node = volta_cfg.get("node")
    if isinstance(volta_node, str) and volta_node:
        return volta_node

    engines = pkg_data.get("engines", {})
    engine_node = engines.get("node")
    if isinstance(engine_node, str) and engine_node:
        cleaned = engine_node.strip()
        base = parse_semver(cleaned.lstrip("^~>=< "))
        return format_semver(base)
    return None


def attempt_node_fix(
    target_version: str,
    auto_fix: bool,
    interactive: bool,
) -> bool:
    volta = shutil.which("volta")
    if not volta:
        logger.warning(
            "Volta is not installed. Install it from https://volta.sh/ to manage Node versions."
        )
        return False

    message = (
        f"Install Node.js {target_version} with Volta using "
        "`volta install node@{version}`?".format(version=target_version)
    )
    run_install = auto_fix or prompt_yes_no(
        message, default=False, interactive=interactive
    )
    if not run_install:
        return False

    install_cmd = [volta, "install", f"node@{target_version}"]
    logger.info("Running: %s", " ".join(install_cmd))
    install_result = run_command(install_cmd)
    if install_result.returncode != 0:
        logger.error("Volta install failed: %s", install_result.stderr.strip())
        return False

    logger.info("Volta installed Node.js %s successfully.", target_version)
    return True


def check_python() -> CheckFailure | None:
    detected_tuple = detect_python_version()
    if detected_tuple >= PYTHON_MIN_VERSION:
        logger.info(
            "Python %s satisfies minimum requirement >= %s",
            format_semver(detected_tuple),
            format_semver(PYTHON_MIN_VERSION),
        )
        return None

    return CheckFailure(
        component="Python",
        requirement=f">= {format_semver(PYTHON_MIN_VERSION)}",
        detected=format_semver(detected_tuple),
        guidance="Upgrade your Python interpreter and recreate the virtual environment.",
    )


def check_node(
    pkg_data: dict,
    auto_fix: bool,
    interactive: bool,
) -> CheckFailure | None:
    engines = pkg_data.get("engines", {})
    node_spec = engines.get("node")
    if not isinstance(node_spec, str) or not node_spec:
        return None

    detected = detect_node_version()
    detected_label = format_semver(detected) if detected else "not installed"

    if detected and satisfies_spec(detected, node_spec):
        logger.info("Node.js %s satisfies requirement %s", detected_label, node_spec)
        return None

    target_version = desired_node_version(pkg_data)
    guidance = f"Install Node.js that satisfies {node_spec}."
    if target_version:
        guidance = f"Install Node.js {target_version} (satisfies {node_spec})."

    failure = CheckFailure(
        component="Node.js",
        requirement=node_spec,
        detected=detected_label,
        guidance=guidance,
    )

    if target_version and attempt_node_fix(
        target_version, auto_fix=auto_fix, interactive=interactive
    ):
        refreshed = detect_node_version()
        if refreshed and satisfies_spec(refreshed, node_spec):
            logger.info(
                "Node.js %s now satisfies requirement %s",
                format_semver(refreshed),
                node_spec,
            )
            return None
        logger.warning("Node.js still does not satisfy the requirement after attempting to fix.")

    return failure


def check_npm(pkg_data: dict) -> CheckFailure | None:
    engines = pkg_data.get("engines", {})
    npm_spec = engines.get("npm")
    if not isinstance(npm_spec, str) or not npm_spec:
        return None

    detected = detect_npm_version()
    detected_label = format_semver(detected) if detected else "not installed"

    if detected and satisfies_spec(detected, npm_spec):
        logger.info("npm %s satisfies requirement %s", detected_label, npm_spec)
        return None

    guidance = f"Update npm to satisfy {npm_spec}."
    return CheckFailure(
        component="npm",
        requirement=npm_spec,
        detected=detected_label,
        guidance=guidance,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Casino Calendar environment checker and fixer.",
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Apply safe fixes without prompting (requires Volta for Node.js).",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Disable interactive prompts (useful in CI environments).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    pkg_data = load_package_metadata()

    interactive = not args.non_interactive and sys.stdin.isatty()

    failures: list[CheckFailure] = []

    python_failure = check_python()
    if python_failure:
        failures.append(python_failure)

    node_failure = check_node(pkg_data, auto_fix=args.auto_fix, interactive=interactive)
    if node_failure:
        failures.append(node_failure)

    npm_failure = check_npm(pkg_data)
    if npm_failure:
        failures.append(npm_failure)

    if not failures:
        logger.info("Environment looks good. All requirements satisfied.")
        return 0

    logger.warning("Detected %d environment issue(s):", len(failures))
    for failure in failures:
        logger.warning(
            "%s: detected %s, requires %s. %s",
            failure.component,
            failure.detected,
            failure.requirement,
            failure.guidance,
        )

    logger.info(
        "Retry this script after addressing the issues. "
        "Use '--auto-fix' with Volta installed to automate Node.js updates."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
