from __future__ import annotations

import re
import sys
from collections.abc import Sequence
from importlib import metadata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
for candidate in (SRC_DIR, PROJECT_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from casino_calendar.logging import config as logging_config  # noqa: E402

logger = logging_config.setup_maintenance_logger(
    "casino_calendar.scripts.verify_requirements"
)


def normalize(name: str) -> str:
    """Normalize package names according to PEP 503."""

    return re.sub(r"[-_.]+", "-", name).lower()


def load_pinned(req_path: Path) -> dict[str, str]:
    """Load pinned package versions from a requirements file."""

    pinned: dict[str, str] = {}
    for raw_line in req_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            continue
        name, ver = line.split("==", 1)
        name = name.split("[", 1)[0].strip()
        ver = ver.split(";", 1)[0].strip()
        if name and ver:
            pinned[normalize(name)] = ver
    return pinned


def installed_versions() -> dict[str, str]:
    """Gather installed package versions."""

    result: dict[str, str] = {}
    for dist in metadata.distributions():
        orig_name = dist.name
        if not orig_name:
            continue
        name = normalize(orig_name)
        result[name] = dist.version
    return result


def main(argv: Sequence[str] | None = None) -> int:
    """Compare pinned requirements against the current environment."""

    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        req_path = Path(args[0]).expanduser()
    else:
        req_path = PROJECT_ROOT / "requirements.txt"

    if not req_path.exists():
        logger.error("Requirements file not found: %s", req_path)
        return 2

    logger.info("Comparing installed packages with %s", req_path)
    pinned = load_pinned(req_path)
    installed = installed_versions()

    mismatches: list[tuple[str, str, str]] = []
    for name, req_ver in pinned.items():
        inst_ver = installed.get(name)
        if inst_ver != req_ver:
            mismatches.append((name, req_ver, inst_ver or "not installed"))

    if mismatches:
        logger.warning("Detected %d package mismatch(es)", len(mismatches))
        for mismatch in mismatches:
            logger.warning(
                "Package %s requires %s but %s is installed",
                mismatch[0],
                mismatch[1],
                mismatch[2],
            )
        return 1

    logger.info("Installed packages match requirements file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
