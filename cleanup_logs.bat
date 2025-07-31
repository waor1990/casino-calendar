@echo off
REM Casino Calendar - Log Cleanup Utility
REM Cleans up old log files and provides log management options

echo Casino Calendar Log Cleanup Utility
echo =====================================

REM Check if virtual environment exists
IF NOT EXIST .venv (
    echo Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo Activating virtual environment...
call .\.venv\Scripts\activate.bat

echo.
if "%1"=="--info" (
    echo Showing log directory information...
    .\.venv\Scripts\python.exe scripts\cleanup_logs.py --info
) else if "%1"=="--archive" (
    echo Archiving current log file...
    .\.venv\Scripts\python.exe scripts\cleanup_logs.py --archive-current
) else if "%1"=="--dry-run" (
    echo Showing what would be deleted keeping 30 days...
    .\.venv\Scripts\python.exe scripts\cleanup_logs.py --days 30 --dry-run
) else (
    echo Cleaning up logs older than 30 days...
    .\.venv\Scripts\python.exe scripts\cleanup_logs.py --days 30
)

echo.
echo Cleanup completed!
echo.
echo Usage examples:
echo   cleanup_logs.bat                 # Clean logs older than 30 days
echo   cleanup_logs.bat --info          # Show log directory info
echo   cleanup_logs.bat --archive       # Archive current log file
echo   cleanup_logs.bat --dry-run       # Preview what would be deleted
echo.

pause
