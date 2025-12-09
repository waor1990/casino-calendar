#!/usr/bin/env python3
"""
Log cleanup utility for Casino Calendar application.

This script can be run manually or scheduled to clean up old log files.
"""
import argparse
import sys
from pathlib import Path

# Add project root/src to Python path (script lives in scripts/python)
project_root = Path(__file__).resolve().parents[2]
src_dir = project_root / "src"
for candidate in (src_dir, project_root):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from casino_calendar.logging import config as logging_config  # type: ignore[import-not-found]  # noqa: E402
from casino_calendar.logging import rotation  # type: ignore[import-not-found]  # noqa: E402

logger = logging_config.setup_maintenance_logger("casino_calendar.scripts.cleanup_logs")


def _file_contains_only_date(file_path: Path, target: str) -> bool:
    """Return True if the log file only contains entries for the target date."""

    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return False

    dates = {line[:10] for line in lines if line.strip() and len(line) >= 10}
    return dates == {target}


def _tidy_log_directory(log_dir: Path) -> None:
    """Ensure only active logs reside at the root; move others to archive or delete."""

    allowed = {
        "casino_calendar_prod.log",
        "casino_calendar_maintenance.log",
        "casino_calendar_http.log",
    }
    archive_dir = log_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    for extra in log_dir.glob("*.log*"):
        if extra.name in allowed:
            continue
        # Delete logs that only contain entries from 2025-10-12
        if _file_contains_only_date(extra, "2025-10-12"):
            try:
                extra.unlink()
            except Exception:
                logger.exception("Could not delete %s", extra)
            continue

        destination = archive_dir / extra.name
        try:
            extra.replace(destination)
        except Exception:
            logger.exception("Could not move %s into archive", extra)

    for active in allowed:
        active_path = log_dir / active
        if active_path.exists():
            rotation.normalise_archives(str(active_path), str(archive_dir))


def main():
    parser = argparse.ArgumentParser(
        description="Clean up old log files for Casino Calendar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/python/cleanup_logs.py --info
  python scripts/python/cleanup_logs.py --archive-by-month --log-file logs/casino_calendar_prod.log
  python scripts/python/cleanup_logs.py --copy-current --log-file logs/casino_calendar_prod.log
  python scripts/python/cleanup_logs.py --copy-split-days 14 --log-file logs/casino_calendar_maintenance.log
        """,
    )

    parser.add_argument(
        "--days", type=int, default=30, help="Number of days to keep logs (default: 30)"
    )
    parser.add_argument(
        "--log-dir", type=str, default="logs", help="Log directory path (default: logs)"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Full path to log file (auto-detect if not provided)",
    )
    parser.add_argument(
        "--archive-dir",
        type=str,
        default=None,
        help="Archive directory (default: <log-dir>/archive)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--info", action="store_true", help="Show information about log directory"
    )
    parser.add_argument(
        "--archive-current",
        action="store_true",
        help="Archive the current production log file",
    )
    parser.add_argument(
        "--archive-split-days",
        type=int,
        default=None,
        help="Archive lines older than N days and trim current log",
    )
    parser.add_argument(
        "--archive-by-month",
        action="store_true",
        help="Archive prior months and keep only current month in active log",
    )
    parser.add_argument(
        "--copy-current",
        action="store_true",
        help="Copy the current log file into the archive directory (no trimming)",
    )
    parser.add_argument(
        "--copy-split-days",
        type=int,
        default=None,
        help="Copy lines older than N days into the archive without trimming",
    )
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")

    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    _tidy_log_directory(log_dir)

    def emit(message: str):
        """Emit an informational message respecting the quiet flag."""
        if args.quiet:
            logger.debug(message)
        else:
            logger.info(message)

    # Determine log file if not supplied
    def resolve_log_file() -> Path:
        if args.log_file:
            return Path(args.log_file)
        # Prefer LOG_FILE env var
        import os

        env_path = os.getenv("LOG_FILE")
        if env_path:
            return Path(env_path)
        # Fallbacks: prefer prod name if it exists
        prod_path = log_dir / "casino_calendar_prod.log"
        default_path = log_dir / "casino_calendar.log"
        if prod_path.exists():
            return prod_path
        return default_path

    # Show log directory info if requested
    if args.info:
        info = rotation.get_log_directory_info(args.log_dir)
        if not info["exists"]:
            logger.warning("Cannot find log directory %s", log_dir)
            return 1

        logger.info("Log directory: %s", log_dir.absolute())
        logger.info("Total files: %s", info["file_count"])
        logger.info(
            "Total size: %.2f MB (%s bytes)",
            info["total_size_mb"],
            f"{info['total_size_bytes']:,}",
        )
        if info["files"]:
            logger.info("Listing files from newest to oldest")
            for file_info in info["files"]:
                logger.info(
                    "%-30s %8.2f MB %s",
                    file_info["name"],
                    file_info["size_mb"],
                    file_info["modified"],
                )
        return 0

    # Archive current log if requested
    if args.archive_current:
        current_log = resolve_log_file()
        if current_log.exists():
            try:
                logger.info("Archiving current log %s", current_log)
                archive_path = rotation.archive_current_log(
                    str(current_log),
                    archive_dir=args.archive_dir,
                )
                rotation.normalise_archives(str(current_log), args.archive_dir)
                logger.info("Archived current log to %s", archive_path)
            except Exception:
                logger.exception("Failed to archive %s", current_log)
                return 1
        else:
            logger.warning("Current log file missing: %s", current_log)
        return 0

    if args.copy_current:
        current_log = resolve_log_file()
        if current_log.exists():
            try:
                logger.info("Copying current log %s into archive", current_log)
                archive_path = rotation.copy_current_log(
                    str(current_log),
                    archive_dir=args.archive_dir,
                )
                logger.info("Copied current log to %s", archive_path)
            except Exception:
                logger.exception("Failed to copy current log %s", current_log)
                return 1
        else:
            logger.warning("Current log file missing: %s", current_log)
        return 0

    # Archive split by days (trim current log)
    if args.archive_split_days is not None:
        log_file = resolve_log_file()
        try:
            logger.info(
                "Archiving entries older than %s day(s) from %s",
                args.archive_split_days,
                log_file,
            )
            summary = rotation.archive_and_trim_by_days(
                str(log_file),
                days_to_keep=args.archive_split_days,
                archive_dir=args.archive_dir,
            )
            files = summary.get("archive_files", [])
            (logger.debug if args.quiet else logger.info)(
                "Archived %d lines into %d file(s) and kept %d lines in %s",
                summary["archived_lines"],
                len(files),
                summary["kept_lines"],
                log_file,
            )
            return 0
        except PermissionError:
            logger.exception(
                "Permission error while writing to %s. Ensure the app is not locking the file.",
                log_file,
            )
            return 1
        except Exception:
            logger.exception("Failed to archive by days for %s", log_file)
            return 1

    # Archive by month (trim current log)
    if args.archive_by_month:
        log_file = resolve_log_file()
        try:
            logger.info("Archiving earlier months for %s", log_file)
            summary = rotation.archive_and_trim_by_month(
                str(log_file), archive_dir=args.archive_dir
            )
            files = summary.get("archive_files", [])
            (logger.debug if args.quiet else logger.info)(
                "Archived %d lines into %d file(s) and kept %d lines in %s",
                summary["archived_lines"],
                len(files),
                summary["kept_lines"],
                log_file,
            )
            return 0
        except PermissionError:
            logger.exception(
                "Permission error while writing to %s. Ensure the app is not locking the file.",
                log_file,
            )
            return 1
        except Exception:
            logger.exception("Failed to archive by month for %s", log_file)
            return 1

    if args.copy_split_days is not None:
        log_file = resolve_log_file()
        try:
            logger.info(
                "Copying entries older than %s day(s) from %s into archive",
                args.copy_split_days,
                log_file,
            )
            summary = rotation.copy_lines_by_days(
                str(log_file),
                args.copy_split_days,
                archive_dir=args.archive_dir,
            )
            files = summary.get("archive_files", [])
            (logger.debug if args.quiet else logger.info)(
                "Copied %d lines into %d archive file(s) from %s",
                summary["copied_lines"],
                len(files),
                log_file,
            )
            return 0
        except Exception:
            logger.exception("Failed to copy by days for %s", log_file)
            return 1

    # Perform cleanup of old files
    if not log_dir.exists():
        logger.warning("Cannot find log directory %s", log_dir)
        return 1

    emit(f"Cleaning up logs older than {args.days} days in {log_dir.absolute()}")

    if args.dry_run:
        emit("Dry run enabled; no files will be deleted")

        import time

        cutoff_time = time.time() - (args.days * 24 * 60 * 60)
        found_files = []

        for log_file in log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                size_mb = log_file.stat().st_size / (1024 * 1024)
                found_files.append((log_file, size_mb))

        if found_files:
            emit("Files scheduled for deletion")
            total_size = 0
            for log_file, size_mb in found_files:
                emit(f"{log_file.name:<30} {size_mb:>8.2f} MB")
                total_size += size_mb
            emit(f"Total files: {len(found_files)}, combined size {total_size:.2f} MB")
        else:
            emit("No files meet deletion criteria")
    else:
        deleted_count = rotation.cleanup_old_logs(args.log_dir, args.days)
        if deleted_count > 0:
            emit(f"Deleted {deleted_count} log file(s)")
        else:
            emit("No log files required deletion")

    return 0


if __name__ == "__main__":
    sys.exit(main())
