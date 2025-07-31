#!/usr/bin/env python3
"""
Log cleanup utility for Casino Calendar application.

This script can be run manually or scheduled to clean up old log files.
"""
import argparse
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.log_rotation import cleanup_old_logs, get_log_directory_info, archive_current_log


def main():
    parser = argparse.ArgumentParser(
        description="Clean up old log files for Casino Calendar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/cleanup_logs.py                    # Default cleanup (30 days)
  python scripts/cleanup_logs.py --days 7          # Keep only 7 days
  python scripts/cleanup_logs.py --dry-run         # Show what would be deleted
  python scripts/cleanup_logs.py --info            # Show log directory info
  python scripts/cleanup_logs.py --archive-current # Archive current log file
        """
    )
    
    parser.add_argument(
        "--days", 
        type=int, 
        default=30, 
        help="Number of days to keep logs (default: 30)"
    )
    parser.add_argument(
        "--log-dir", 
        type=str, 
        default="logs", 
        help="Log directory path (default: logs)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--info", 
        action="store_true", 
        help="Show information about log directory"
    )
    parser.add_argument(
        "--archive-current", 
        action="store_true", 
        help="Archive the current production log file"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true", 
        help="Reduce output verbosity"
    )
    
    args = parser.parse_args()
    
    log_dir = Path(args.log_dir)
    
    # Show log directory info if requested
    if args.info:
        info = get_log_directory_info(args.log_dir)
        if not info["exists"]:
            print(f"Log directory {log_dir} does not exist")
            return 1
        
        print(f"Log Directory: {log_dir.absolute()}")
        print(f"Total files: {info['file_count']}")
        print(f"Total size: {info['total_size_mb']:.2f} MB ({info['total_size_bytes']:,} bytes)")
        print()
        
        if info['files']:
            print("Files (newest first):")
            for file_info in info['files']:
                print(f"  {file_info['name']:<30} {file_info['size_mb']:>8.2f} MB  {file_info['modified']}")
        return 0
    
    # Archive current log if requested
    if args.archive_current:
        current_log = log_dir / "casino_calendar_prod.log"
        if current_log.exists():
            try:
                archive_path = archive_current_log(str(current_log))
                print(f"Archived current log to: {archive_path}")
            except Exception as e:
                print(f"Error archiving current log: {e}")
                return 1
        else:
            print(f"Current log file {current_log} does not exist")
        return 0
    
    # Perform cleanup
    if not log_dir.exists():
        print(f"Log directory {log_dir} does not exist")
        return 1
    
    if not args.quiet:
        print(f"Cleaning up logs older than {args.days} days in {log_dir.absolute()}")
    
    if args.dry_run:
        print("DRY RUN - No files will be deleted")
        print()
        
        import time
        cutoff_time = time.time() - (args.days * 24 * 60 * 60)
        found_files = []
        
        for log_file in log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                size_mb = log_file.stat().st_size / (1024 * 1024)
                found_files.append((log_file, size_mb))
        
        if found_files:
            print("Files that would be deleted:")
            total_size = 0
            for log_file, size_mb in found_files:
                print(f"  {log_file.name:<30} {size_mb:>8.2f} MB")
                total_size += size_mb
            print(f"\nTotal: {len(found_files)} files, {total_size:.2f} MB")
        else:
            print("No files found that match deletion criteria")
    else:
        deleted_count = cleanup_old_logs(args.log_dir, args.days)
        if not args.quiet:
            if deleted_count > 0:
                print(f"Deleted {deleted_count} old log files")
            else:
                print("No old log files found to delete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
