@echo off
REM Casino Calendar - REST API Startup Script
REM Starts the Flask REST API server on port 5001

setlocal enabledelayedexpansion

echo ================================================
echo Casino Calendar - REST API
echo ================================================

REM Get the project root directory
set "SCRIPT_DIR=%~dp0"
for %%A in ("!SCRIPT_DIR!\..\..\") do set "PROJECT_ROOT=%%~fA"

REM Change to project directory
cd /d "!PROJECT_ROOT!"

echo Working directory: !PROJECT_ROOT!
echo.

REM Check for virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found
    echo Please run: scripts\windows\setup.bat first
    pause
    exit /b 1
)

echo [OK] Virtual environment found
set "PYTHON_EXE=!PROJECT_ROOT!\.venv\Scripts\python.exe"
echo [OK] Python executable: !PYTHON_EXE!
echo.

REM Enable UTF-8 console support
chcp 65001 >nul 2>&1

echo Starting REST API...
echo.
echo Server will be available at: http://localhost:5001
echo Press Ctrl+C to stop the server
echo.

"!PYTHON_EXE!" api/event_api.py

endlocal
