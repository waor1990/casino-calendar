@echo off
setlocal enabledelayedexpansion

REM Resolve project root
for %%I in ("%~dp0\..\..") do set "ROOT_DIR=%%~fI"
cd /d "%ROOT_DIR%"

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found
    echo Please run scripts\windows\setup.bat first
    pause
    exit /b 1
)

set "PYTHONPATH=%CD%\src;%CD%"
set "PYTHONIOENCODING=utf-8"

.venv\Scripts\python.exe "scripts\python\run_tests.py"
exit /b %ERRORLEVEL%
