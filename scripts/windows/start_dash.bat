@echo off
REM Casino Calendar - Dash App Startup Script
REM Starts the Dash application on port 8050
REM NOTE: Requires the REST API to be running (on port 5001)

setlocal enabledelayedexpansion

echo ================================================
echo Casino Calendar - Dash Application
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

REM Build CSS first
echo Building CSS from SCSS...
where npm >nul 2>&1
if errorlevel 1 (
    echo [WARNING] npm not found, skipping CSS build
) else (
    echo [INFO] npm found, attempting CSS build...
    call npm run build:css >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] CSS build failed, but continuing...
    ) else (
        echo [OK] CSS built successfully
    )
)
echo.

echo Starting Dash Application...
echo.
echo NOTE: This script assumes the REST API is already running on http://localhost:5001
echo If the API is not running, the app will wait for it to become available
echo.
echo Dash App will be available at: http://localhost:8050
echo Press Ctrl+C to stop the server
echo.

"!PYTHON_EXE!" app.py

endlocal
