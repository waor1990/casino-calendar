"""
Log rotation and cleanup utilities for Casino Calendar application.
"""

import logging
import logging.handlers
import shutil
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


def setup_rotating_logger(
    name: str,
    log_file: str,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True,
) -> logging.Logger:
    """
    Set up a rotating file handler for logs with optional console output.

    Args:
        name: Logger name
        log_file: Path to log file
        level: Logging level
        max_bytes: Maximum size per log file (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
        console_output: Whether to also output to console

    Returns:
        Configured logger instance
    """
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        # Set console to WARNING level to reduce noise
        console_handler.setLevel(logging.WARNING)
        logger.addHandler(console_handler)

    return logger


def cleanup_old_logs(log_directory: str, days_to_keep: int = 30) -> int:
    """
    Clean up log files older than specified days.

    Args:
        log_directory: Directory containing log files
        days_to_keep: Number of days to keep logs (default: 30)

    Returns:
        Number of files deleted
    """
    log_dir = Path(log_directory)
    if not log_dir.exists():
        return 0

    cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
    deleted_count = 0

    # Look for log files (including rotated ones)
    for log_file in log_dir.glob("*.log*"):
        try:
            if log_file.stat().st_mtime < cutoff_time:
                file_size = log_file.stat().st_size
                log_file.unlink()
                print(f"Deleted old log file: {log_file} ({file_size:,} bytes)")
                deleted_count += 1
        except Exception as e:
            print(f"Error deleting {log_file}: {e}")

    return deleted_count


def get_log_directory_info(log_directory: str) -> dict:
    """
    Get information about the log directory.

    Args:
        log_directory: Directory containing log files

    Returns:
        Dictionary with log directory statistics
    """
    log_dir = Path(log_directory)
    if not log_dir.exists():
        return {"exists": False}

    log_files = list(log_dir.glob("*.log*"))
    total_size = sum(f.stat().st_size for f in log_files)

    return {
        "exists": True,
        "file_count": len(log_files),
        "total_size_bytes": total_size,
        "total_size_mb": total_size / (1024 * 1024),
        "files": [
            {
                "name": f.name,
                "size_bytes": f.stat().st_size,
                "size_mb": f.stat().st_size / (1024 * 1024),
                "modified": time.ctime(f.stat().st_mtime),
            }
            for f in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)
        ],
    }


def archive_current_log(
    log_file: str,
    archive_suffix: Optional[str] = None,
    archive_dir: Optional[str] = None,
    move: bool = True,
) -> str:
    """
    Archive the current log file before implementing rotation.

    Args:
        log_file: Path to the current log file
        archive_suffix: Optional suffix for the archive (defaults to timestamp)
        archive_dir: Optional directory where archives are stored
        move: When True move the file, otherwise copy

    Returns:
        Path to the archived file
    """
    log_path = Path(log_file)
    if not log_path.exists():
        raise FileNotFoundError(f"Log file {log_file} does not exist")

    # Normalize archive_dir to a Path for local operations
    if archive_dir is None:
        arch_dir = log_path.parent / "archive"
    else:
        arch_dir = Path(archive_dir)
    arch_dir.mkdir(parents=True, exist_ok=True)

    if archive_suffix is None:
        archive_suffix = time.strftime("%Y%m%d_%H%M%S")

    archive_name = f"{log_path.stem}_{archive_suffix}{log_path.suffix}"
    archive_path = arch_dir / archive_name

    if move:
        log_path.replace(archive_path)
    else:
        shutil.copy2(log_path, archive_path)

    return str(archive_path)


def _parse_log_timestamp(line: str) -> Optional[datetime]:
    """
    Parse timestamp at start of a log line using the project's formatter
    "YYYY-MM-DD HH:MM:SS | ...". Returns None if not parseable.
    """
    if len(line) < 19:
        return None
    ts_str = line[:19]
    try:
        # Logs are local time; parse as naive datetime
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _replace_with_retry(
    src: Path, dest: Path, attempts: int = 5, delay: float = 0.2
) -> None:
    """Replace ``dest`` with ``src`` retrying on ``PermissionError`` (Windows)."""

    last_exc: Optional[PermissionError] = None
    for attempt in range(1, attempts + 1):
        try:
            src.replace(dest)
            return
        except PermissionError as exc:  # pragma: no cover - platform specific
            last_exc = exc
            if attempt == attempts:
                break
            time.sleep(delay)
    if last_exc is not None:
        raise last_exc


def _write_lines_with_fallback(dest: Path, lines: List[str]) -> None:
    """Write ``lines`` to ``dest`` handling Windows file locks gracefully."""

    tmp_path = dest.with_suffix(dest.suffix + ".tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as tmp_file:
            tmp_file.writelines(lines)

        try:
            _replace_with_retry(tmp_path, dest)
            return
        except PermissionError as replace_exc:
            try:
                with dest.open("r+", encoding="utf-8") as existing:
                    existing.seek(0)
                    existing.writelines(lines)
                    existing.truncate()
            except PermissionError:
                raise replace_exc
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


def _normalise_line_endings(lines: Iterable[str]) -> List[str]:
    """Ensure each line ends with a newline and return as list."""

    normalised: List[str] = []
    for line in lines:
        if not line.endswith("\n"):
            line = f"{line}\n"
        normalised.append(line)
    return normalised


def _dedupe_and_sort_lines(lines: Iterable[str]) -> List[str]:
    """Return unique log lines sorted by timestamp then original order."""

    unique_lines: List[Tuple[datetime, int, str]] = []
    seen = set()
    for index, raw_line in enumerate(_normalise_line_endings(lines)):
        if raw_line in seen:
            continue
        seen.add(raw_line)
        timestamp = _parse_log_timestamp(raw_line) or datetime.min
        unique_lines.append((timestamp, index, raw_line))

    unique_lines.sort(key=lambda item: (item[0], item[1]))
    return [entry[2] for entry in unique_lines]


def _month_key(dt: Optional[datetime]) -> Optional[str]:
    """Return YYYY-MM month key for datetime."""

    if dt is None:
        return None
    return dt.strftime("%Y-%m")


def _merge_month_archive(
    base_name: str,
    month_key: str,
    archive_dir: Path,
    lines: Iterable[str],
) -> None:
    """Merge ``lines`` into the per-month archive file."""

    if not lines:
        return

    month_file = archive_dir / f"{base_name}_{month_key}.log"
    existing: List[str] = []
    if month_file.exists():
        existing = month_file.read_text(encoding="utf-8").splitlines(True)

    merged = _dedupe_and_sort_lines(existing + list(lines))
    _write_lines_with_fallback(month_file, merged)


def _append_to_all_archive(
    base_name: str, archive_dir: Path, lines: Iterable[str]
) -> None:
    """Append ``lines`` to the global archive, keeping unique entries."""

    if not lines:
        return

    all_file = archive_dir / f"{base_name}_all.log"
    existing: List[str] = []
    if all_file.exists():
        existing = all_file.read_text(encoding="utf-8").splitlines(True)

    merged = _dedupe_and_sort_lines(existing + list(lines))
    _write_lines_with_fallback(all_file, merged)


def _rebucket_existing_archives(log_path: Path, archive_dir: Path) -> None:
    """Ensure existing archive files are normalised into per-month files."""

    base_name = log_path.stem
    month_map: Dict[str, List[str]] = defaultdict(list)

    # Collect lines from existing files
    for file_path in archive_dir.glob("*.log"):
        # If another process removed the file between globbing and handling,
        # ignore FileNotFoundError and continue.
        if file_path.name == f"{base_name}_all.log":
            try:
                file_path.unlink()
            except FileNotFoundError:
                # already removed concurrently; ignore
                pass
            continue
        if not file_path.name.startswith(base_name):
            continue

        try:
            lines = file_path.read_text(encoding="utf-8").splitlines(True)
        except FileNotFoundError:
            # file disappeared between listing and read; skip it
            continue
        if not lines:
            try:
                file_path.unlink()
            except FileNotFoundError:
                pass
            continue

        # If the entire file only contains logs from 2025-10-12, drop it
        distinct_dates = set()
        for line in lines:
            dt = _parse_log_timestamp(line)
            distinct_dates.add(dt.date() if dt is not None else None)
        if distinct_dates == {datetime(2025, 10, 12).date()}:
            file_path.unlink()
            continue

        for line in lines:
            dt = _parse_log_timestamp(line)
            key = _month_key(dt)
            if key:
                month_map[key].append(line)

        file_path.unlink()

    # Recreate per-month files and all-file
    for month_key, month_lines in month_map.items():
        _merge_month_archive(base_name, month_key, archive_dir, month_lines)

    combined_lines = [line for month in sorted(month_map) for line in month_map[month]]
    _append_to_all_archive(base_name, archive_dir, combined_lines)


def archive_and_trim_by_days(
    log_file: str,
    days_to_keep: int = 30,
    archive_dir: Optional[str] = None,
) -> Dict[str, object]:
    """
    Archive all log lines older than N days into a single archive file and
    trim the current log to keep only the last N days.

    Returns a summary dict with counts and archive path (if any).
    """
    log_path = Path(log_file)
    if not log_path.exists():
        raise FileNotFoundError(f"Log file {log_file} does not exist")

    # Normalize archive_dir to a Path for local operations
    if archive_dir is None:
        arch_dir = log_path.parent / "archive"
    else:
        arch_dir = Path(archive_dir)
    arch_dir.mkdir(parents=True, exist_ok=True)

    cutoff_ts = time.time() - (days_to_keep * 24 * 60 * 60)

    archived_lines: List[str] = []
    recent_lines: List[str] = []

    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            dt = _parse_log_timestamp(line)
            if dt is None:
                recent_lines.append(line)
                continue
            if dt.timestamp() < cutoff_ts:
                archived_lines.append(line)
            else:
                recent_lines.append(line)

    archived_count = 0
    kept_count = len(recent_lines)

    archived_files: List[str] = []
    archived_payload: List[str] = []
    if archived_lines:
        _rebucket_existing_archives(log_path, arch_dir)

        buckets: Dict[str, List[str]] = defaultdict(list)
        for line in archived_lines:
            dt = _parse_log_timestamp(line)
            month = _month_key(dt)
            if month:
                buckets[month].append(line)

        base_name = log_path.stem
        for month_key, month_lines in buckets.items():
            # Skip files that would contain only 2025-10-12 entries
            dates = set()
            for line in month_lines:
                dt = _parse_log_timestamp(line)
                dates.add(dt.date() if dt is not None else None)
            if dates == {datetime(2025, 10, 12).date()}:
                continue

            _merge_month_archive(base_name, month_key, arch_dir, month_lines)
            archived_files.append(str(arch_dir / f"{base_name}_{month_key}.log"))
            archived_payload.extend(month_lines)

    _append_to_all_archive(base_name, arch_dir, archived_payload)
    archived_count = len(archived_payload)

    _write_lines_with_fallback(log_path, recent_lines)

    return {
        "archived_lines": archived_count,
        "kept_lines": kept_count,
        "archive_files": archived_files,
    }


def archive_and_trim_by_month(
    log_file: str, archive_dir: Optional[str] = None
) -> Dict[str, object]:
    """
    Archive log lines into per-month files (YYYY-MM) and keep only the current
    month's logs in the active file. Returns a summary dict.
    """
    log_path = Path(log_file)
    if not log_path.exists():
        raise FileNotFoundError(f"Log file {log_file} does not exist")

    # Normalize archive_dir to a Path for local operations
    if archive_dir is None:
        arch_dir = log_path.parent / "archive"
    else:
        arch_dir = Path(archive_dir)
    arch_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    current_key = now.strftime("%Y-%m")

    _rebucket_existing_archives(log_path, arch_dir)

    buckets: Dict[str, List[str]] = {}
    kept_lines: List[str] = []

    with log_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            dt = _parse_log_timestamp(line)
            if dt is None:
                # Attach non-parseable lines to kept (current month) to avoid losing metadata headers
                kept_lines.append(line)
                continue
            key = dt.strftime("%Y-%m")
            if key == current_key:
                kept_lines.append(line)
            else:
                buckets.setdefault(key, []).append(line)

    archive_files: List[str] = []
    archived_payload: List[str] = []
    base = log_path.stem

    for key, lines in buckets.items():
        dates = set()
        for line in lines:
            dt = _parse_log_timestamp(line)
            dates.add(dt.date() if dt is not None else None)
        if dates == {datetime(2025, 10, 12).date()}:
            continue

        _merge_month_archive(base, key, arch_dir, lines)
        archive_files.append(str(arch_dir / f"{base}_{key}.log"))
        archived_payload.extend(lines)

    _append_to_all_archive(base, arch_dir, archived_payload)

    _write_lines_with_fallback(log_path, kept_lines)

    total_archived = len(archived_payload)
    return {
        "archived_lines": total_archived,
        "kept_lines": len(kept_lines),
        "archive_files": archive_files,
    }


def copy_lines_by_days(
    log_file: str,
    days: int,
    archive_dir: Optional[str] = None,
) -> Dict[str, object]:
    """Copy lines older than ``days`` into archive files without trimming."""

    log_path = Path(log_file)
    if not log_path.exists():
        raise FileNotFoundError(f"Log file {log_file} does not exist")

    # Normalize archive_dir to a Path for local operations
    if archive_dir is None:
        arch_dir = log_path.parent / "archive"
    else:
        arch_dir = Path(archive_dir)
    arch_dir.mkdir(parents=True, exist_ok=True)

    cutoff_ts = time.time() - (days * 24 * 60 * 60)
    copied_lines: List[str] = []

    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            dt = _parse_log_timestamp(line)
            if dt is None:
                continue
            if dt.timestamp() < cutoff_ts:
                copied_lines.append(line)

    if not copied_lines:
        return {"copied_lines": 0, "archive_files": []}

    _rebucket_existing_archives(log_path, arch_dir)

    base = log_path.stem
    buckets: Dict[str, List[str]] = defaultdict(list)
    for line in copied_lines:
        month = _month_key(_parse_log_timestamp(line))
        if month:
            buckets[month].append(line)

    archive_files: List[str] = []
    copied_payload: List[str] = []
    for month_key, month_lines in buckets.items():
        dates = set()
        for line in month_lines:
            dt = _parse_log_timestamp(line)
            dates.add(dt.date() if dt is not None else None)
        if dates == {datetime(2025, 10, 12).date()}:
            continue

        _merge_month_archive(base, month_key, arch_dir, month_lines)
        archive_files.append(str(arch_dir / f"{base}_{month_key}.log"))
        copied_payload.extend(month_lines)

    _append_to_all_archive(base, arch_dir, copied_payload)

    return {"copied_lines": len(copied_payload), "archive_files": archive_files}


def copy_current_log(log_file: str, archive_dir: Optional[str] = None) -> str:
    """Copy the current log file into the archive directory without trimming."""

    log_path = Path(log_file)
    if archive_dir is None:
        arch_dir = log_path.parent / "archive"
    else:
        arch_dir = Path(archive_dir)
    arch_dir.mkdir(parents=True, exist_ok=True)

    _rebucket_existing_archives(log_path, arch_dir)

    archive_path = Path(
        archive_current_log(log_file, archive_dir=str(arch_dir), move=False)
    )
    lines = archive_path.read_text(encoding="utf-8").splitlines(True)
    buckets: Dict[str, List[str]] = defaultdict(list)
    for line in lines:
        month = _month_key(_parse_log_timestamp(line))
        if month:
            buckets[month].append(line)

    payload: List[str] = []
    for month_key, month_lines in buckets.items():
        dates = set()
        for line in month_lines:
            dt = _parse_log_timestamp(line)
            dates.add(dt.date() if dt is not None else None)
        if dates == {datetime(2025, 10, 12).date()}:
            continue

        _merge_month_archive(log_path.stem, month_key, arch_dir, month_lines)
        payload.extend(month_lines)

    _append_to_all_archive(log_path.stem, arch_dir, payload)

    return str(archive_path)


def normalise_archives(log_file: str, archive_dir: Optional[str] = None) -> None:
    """Public helper to normalise archive structure for ``log_file``."""

    log_path = Path(log_file)
    if archive_dir is None:
        arch_dir = log_path.parent / "archive"
    else:
        arch_dir = Path(archive_dir)
    arch_dir.mkdir(parents=True, exist_ok=True)

    _rebucket_existing_archives(log_path, arch_dir)
