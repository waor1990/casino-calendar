"""
Log rotation and cleanup utilities for Casino Calendar application.
"""

import logging
import logging.handlers
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


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


def archive_current_log(log_file: str, archive_suffix: Optional[str] = None) -> str:
    """
    Archive the current log file before implementing rotation.

    Args:
        log_file: Path to the current log file
        archive_suffix: Optional suffix for the archive (defaults to timestamp)

    Returns:
        Path to the archived file
    """
    log_path = Path(log_file)
    if not log_path.exists():
        raise FileNotFoundError(f"Log file {log_file} does not exist")

    if archive_suffix is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        archive_suffix = f"backup_{timestamp}"

    archive_name = f"{log_path.stem}_{archive_suffix}{log_path.suffix}"
    archive_path = log_path.parent / archive_name

    # Move the current log to archive
    log_path.rename(archive_path)

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

    if archive_dir is None:
        archive_dir = str(log_path.parent / "archive")

    arch_dir = Path(archive_dir)
    arch_dir.mkdir(parents=True, exist_ok=True)

    cutoff_ts = time.time() - (days_to_keep * 24 * 60 * 60)

    archived_lines: List[str] = []
    recent_lines: List[str] = []
    archived_dates: List[datetime] = []

    with log_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            dt = _parse_log_timestamp(line)
            if dt is None:
                # If we have already started collecting recent lines, keep unparseable lines with the most recent section
                # Otherwise, send with archived section to avoid losing header context
                target = recent_lines if recent_lines else archived_lines
                target.append(line)
                continue
            if dt.timestamp() < cutoff_ts:
                archived_lines.append(line)
                archived_dates.append(dt)
            else:
                recent_lines.append(line)

    archive_path_str: Optional[str] = None
    archived_count = len(archived_lines)
    kept_count = len(recent_lines)

    if archived_lines:
        # Determine date range
        first_dt = min(archived_dates)
        last_dt = max(archived_dates)
        base = log_path.stem  # e.g., casino_calendar_prod
        suffix = log_path.suffix  # e.g., .log
        range_str = f"{first_dt.strftime('%Y%m%d')}-{last_dt.strftime('%Y%m%d')}"
        archive_file = arch_dir / f"{base}_{range_str}{suffix}"
        with archive_file.open("w", encoding="utf-8") as af:
            af.writelines(archived_lines)
        archive_path_str = str(archive_file)

    # Rewrite current log with recent lines only (atomic-ish replace)
    tmp_path = log_path.with_suffix(log_path.suffix + ".tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as tf:
            tf.writelines(recent_lines)
        tmp_path.replace(log_path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass

    return {
        "archived_lines": archived_count,
        "kept_lines": kept_count,
        "archive_path": archive_path_str,
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

    if archive_dir is None:
        archive_dir = str(log_path.parent / "archive")

    arch_dir = Path(archive_dir)
    arch_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    current_key = now.strftime("%Y-%m")

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
    base = log_path.stem
    suffix = log_path.suffix

    for key, lines in buckets.items():
        archive_file = arch_dir / f"{base}_{key}{suffix}"
        with archive_file.open("a", encoding="utf-8") as af:
            af.writelines(lines)
        archive_files.append(str(archive_file))

    # Rewrite current log with current month lines only
    tmp_path = log_path.with_suffix(log_path.suffix + ".tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as tf:
            tf.writelines(kept_lines)
        tmp_path.replace(log_path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass

    total_archived = sum(len(v) for v in buckets.values())
    return {
        "archived_lines": total_archived,
        "kept_lines": len(kept_lines),
        "archive_files": archive_files,
    }
