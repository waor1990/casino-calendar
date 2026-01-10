@echo off
setlocal enabledelayedexpansion

REM Resolve project root
for %%I in ("%~dp0\..\..") do set "ROOT_DIR=%%~fI"

echo.
echo Casino Calendar - Scheduled Log Cleanup Creator
echo.

if not exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found
    exit /b 1
)

set "PYTHONIOENCODING=utf-8"
%ROOT_DIR%\.venv\Scripts\python.exe "%ROOT_DIR%\scripts\python\cleanup_logs.py" --schedule
exit /b %ERRORLEVEL%
