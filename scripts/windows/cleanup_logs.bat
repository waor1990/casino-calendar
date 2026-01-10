@echo off
setlocal enabledelayedexpansion

REM Resolve project root
for %%I in ("%~dp0\..\..") do set "ROOT_DIR=%%~fI"

echo.
echo Casino Calendar - Log Cleanup Utility
echo.
echo Cleaning up rotated log files in: %ROOT_DIR%\logs\archive
echo.

if not exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found
    exit /b 1
)

set "PYTHONIOENCODING=utf-8"
%ROOT_DIR%\.venv\Scripts\python.exe "%ROOT_DIR%\scripts\python\cleanup_logs.py" %*
exit /b %ERRORLEVEL%
