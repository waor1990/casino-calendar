@echo off
REM Casino Calendar - Log Cleanup Utility
REM Cleans up old log files and provides log management options

echo Casino Calendar Log Cleanup Utility
echo =====================================

REM Navigate to project root (parent of tools directory)
cd /d "%~dp0\.."

REM Check if virtual environment exists
IF NOT EXIST .venv (
    echo Virtual environment not found. Please run tools\setup.bat first.
    pause
    exit /b 1
)

echo Activating virtual environment...
call .\.venv\Scripts\activate.bat

echo.
REM If no arguments, prompt the user for desired action
if "%~1"=="" goto MENU

if "%1"=="--info" (
    echo Showing log directory information...
    .\.venv\Scripts\python.exe scripts\maintenance\cleanup_logs.py --info
) else if "%1"=="--archive" (
    echo Archiving current log file...
    .\.venv\Scripts\python.exe scripts\maintenance\cleanup_logs.py --archive-current
) else if "%1"=="--by-month" (
    echo Archiving prior months and keeping only current month in active log...
    .\.venv\Scripts\python.exe scripts\maintenance\cleanup_logs.py --archive-by-month
) else if "%1"=="--dry-run" (
    echo Showing what would be deleted keeping 30 days...
    .\.venv\Scripts\python.exe scripts\maintenance\cleanup_logs.py --days 30 --dry-run
) else (
    echo Unknown option: %1
    echo.
    goto USAGE
)

echo.
echo Cleanup completed!
echo.
echo Press any key to exit . . .
pause >nul
exit /b 0

:MENU
echo Select how you want to archive the LOG_FILE:
echo   [1] Archive lines older than 30 days and trim current log
echo   [2] Archive by month (keep only current month in active log)
echo   [3] Archive current log file (full-file archive)
echo   [4] Show log directory info
echo   [5] Custom days: archive-and-trim (enter days)
echo   [6] Exit
set /p CHOICE=Enter choice [1-6]: 

if "%CHOICE%"=="1" goto OPT1_SPLIT30
if "%CHOICE%"=="2" goto OPT2_BYMONTH
if "%CHOICE%"=="3" goto OPT3_ARCHIVE
if "%CHOICE%"=="4" goto OPT4_INFO
if "%CHOICE%"=="5" goto OPT5_CUSTOM
if "%CHOICE%"=="6" goto END

echo.
echo Invalid choice.
echo.
goto MENU

:OPT1_SPLIT30
echo Archiving lines older than 30 days and trimming current log...
.\.venv\Scripts\python.exe scripts\maintenance\cleanup_logs.py --archive-split-days 30
goto END

:OPT2_BYMONTH
echo Archiving prior months and keeping only current month in active log...
.\.venv\Scripts\python.exe scripts\maintenance\cleanup_logs.py --archive-by-month
goto END

:OPT3_ARCHIVE
echo Archiving current log file...
.\.venv\Scripts\python.exe scripts\maintenance\cleanup_logs.py --archive-current
goto END

:OPT4_INFO
echo Showing log directory information...
.\.venv\Scripts\python.exe scripts\maintenance\cleanup_logs.py --info
goto END

:OPT5_CUSTOM
set /p DAYS=Enter number of days to keep (e.g., 30): 
if "%DAYS%"=="" goto MENU
echo Archiving lines older than %DAYS% days and trimming current log...
.\.venv\Scripts\python.exe scripts\maintenance\cleanup_logs.py --archive-split-days %DAYS%
goto END

:USAGE
echo Usage:
echo   tools\cleanup_logs.bat                 ^(interactive menu^)
echo   tools\cleanup_logs.bat --info          ^(show log directory info^)
echo   tools\cleanup_logs.bat --archive       ^(archive current log file^)
echo   tools\cleanup_logs.bat --by-month      ^(archive by month, keep current month^)
echo   tools\cleanup_logs.bat --dry-run       ^(preview deletion of files older than 30 days^)
echo.
echo Press any key to exit . . .
pause >nul
exit /b 1

:END
echo.
echo Done.
echo.
echo Press any key to exit . . .
pause >nul
exit /b 0
