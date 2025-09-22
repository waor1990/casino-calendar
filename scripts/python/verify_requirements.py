from __future__ import annotations

import re
import sys
from collections.abc import Sequence
from importlib import metadata
from pathlib import Path


def normalize(name: str) -> str:
    # Normalize according to PEP 503 so ``requests`` and ``Requests`` match
    return re.sub(r"[-_.]+", "-", name).lower()


def load_pinned(req_path: Path) -> dict[str, str]:
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
    result: dict[str, str] = {}
    for dist in metadata.distributions():
        orig_name = dist.name
        if not orig_name:
            continue
        name = normalize(orig_name)
        result[name] = dist.version
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        req_path = Path(args[0]).expanduser()
    else:
        req_path = Path(__file__).resolve().parent.parent / "requirements.txt"
    if not req_path.exists():
        print("requirements.txt not found", file=sys.stderr)
        return 2
    pinned = load_pinned(req_path)
    installed = installed_versions()

    mismatches: list[str] = []
    for name, req_ver in pinned.items():
        inst_ver = installed.get(name)
        if inst_ver != req_ver:
            mismatches.append(f"- {name} required {req_ver}, installed {inst_ver or 'not installed'}")

    if mismatches:
        print("\n".join(mismatches))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
