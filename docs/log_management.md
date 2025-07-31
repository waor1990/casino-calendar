# Log Management Guide for Casino Calendar

This guide explains how to manage log files effectively in the Casino Calendar application.

## Overview

The application now includes automatic log rotation and cleanup features to prevent log files from growing too large and consuming excessive disk space.

## Current Log Setup

### Log Files

- **Main log**: `logs/casino_calendar.log` (with automatic rotation)
- **Legacy log**: `logs/casino_calendar_prod.log` (to be phased out)

### Rotation Settings

- **Max file size**: 10MB per log file
- **Backup count**: 5 files (total ~50MB)
- **File naming**: `casino_calendar.log`, `casino_calendar.log.1`, `casino_calendar.log.2`, etc.

## Manual Log Management

### Check Log Directory Information

```bash
# Using batch file
tools\cleanup_logs.bat --info

# Using Python directly
python scripts\maintenance\cleanup_logs.py --info
```

### Preview What Would Be Deleted

```bash
# Show files older than 30 days (default)
tools\cleanup_logs.bat --dry-run

# Show files older than 7 days
python scripts\maintenance\cleanup_logs.py --days 7 --dry-run
```

### Clean Up Old Logs

```bash
# Clean logs older than 30 days
tools\cleanup_logs.bat

# Clean logs older than specific days
python scripts\maintenance\cleanup_logs.py --days 7
```

### Archive Current Log

```bash
# Archive the current production log
tools\cleanup_logs.bat --archive

# Archive with custom name
python scripts\maintenance\cleanup_logs.py --archive-current
```

## Automated Cleanup

### Option 1: Windows Task Scheduler (Recommended)

1. Run as Administrator: `scripts\maintenance\create_scheduled_cleanup.bat`
2. This creates a weekly task that runs every Sunday at 2:00 AM
3. Automatically cleans logs older than 30 days

### Option 2: Manual Scheduled Task

```cmd
# Create task manually
schtasks /create /tn "Casino Calendar Log Cleanup" /tr "C:\path\to\project\.venv\Scripts\python.exe C:\path\to\project\scripts\cleanup_logs.py --days 30 --quiet" /sc weekly /d SUN /st 02:00

# View the task
schtasks /query /tn "Casino Calendar Log Cleanup"

# Run task manually
schtasks /run /tn "Casino Calendar Log Cleanup"

# Delete task
schtasks /delete /tn "Casino Calendar Log Cleanup" /f
```

## Log Retention Recommendations

### Development Environment

- **Retention**: 7 days
- **Reason**: Frequent testing generates many logs, shorter retention saves space

### Production Environment  

- **Retention**: 30-90 days
- **Reason**: Longer retention helps with debugging issues that might surface later

### Critical Systems

- **Retention**: 1 year
- **Reason**: Compliance and audit requirements

## Log Size Management

### Current Space Usage

After cleanup, the log directory should typically use:

- **Active logs**: ~10-50MB (depending on application activity)
- **Archived logs**: Varies based on retention period

### Warning Signs

- Log directory > 500MB
- Individual files > 10MB (rotation not working)
- Very old files present (cleanup not running)

## Troubleshooting

### Log Rotation Not Working

1. Check file permissions on log directory
2. Verify application has write access
3. Check for file locks (application using the log file)

### Cleanup Script Issues

```bash
# Test the cleanup script
python scripts\maintenance\cleanup_logs.py --info

# Check if virtual environment is activated
.venv\Scripts\python.exe --version

# Verify script permissions
dir scripts\cleanup_logs.py
```

### Scheduled Task Not Running

1. Check task exists: `schtasks /query /tn "Casino Calendar Log Cleanup"`
2. Check task history in Task Scheduler GUI
3. Run manually to test: `schtasks /run /tn "Casino Calendar Log Cleanup"`
4. Verify paths in task definition are absolute paths

## Best Practices

### For Developers

1. **Use appropriate log levels**:
   - DEBUG: Detailed information for debugging
   - INFO: General information about application flow
   - WARNING: Something unexpected but not critical
   - ERROR: Error conditions that don't stop the application
   - CRITICAL: Serious errors that might stop the application

2. **Avoid logging sensitive information**:
   - No passwords, tokens, or personal data
   - Sanitize user inputs before logging

3. **Use structured logging**:
   - Include context (user ID, session ID, etc.)
   - Use consistent formatting

### For System Administrators

1. **Monitor log disk usage**: Set up alerts if logs consume too much space
2. **Regular backups**: Include important logs in backup strategy
3. **Security**: Protect log files from unauthorized access
4. **Performance**: Monitor log I/O impact on application performance

## Configuration Files

### Environment Variables

Set these in your `.env` file or environment:

```env
LOG_LEVEL=INFO                    # Set log level
LOG_FILE=logs/casino_calendar.log # Set log file path
```

### Application Configuration

The application automatically:

- Creates log directory if it doesn't exist
- Sets up rotation (10MB files, 5 backups)
- Cleans up old logs on startup (30 days retention)
- Uses appropriate log levels for console vs file output

## Migration from Old Logging

If you have existing `casino_calendar_prod.log` files:

1. Archive them: `cleanup_logs.bat --archive`
2. The new system will create `casino_calendar.log` with rotation
3. Update any log monitoring tools to use the new file names

## Support

For issues with log management:

1. Check this documentation first
2. Review the cleanup script help: `python scripts\maintenance\cleanup_logs.py --help`
3. Check application logs for any logging-related errors
4. Verify file permissions and disk space
