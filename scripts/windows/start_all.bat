@echo off
REM Casino Calendar - Complete Application Startup
REM This script starts both the REST API and the Dash application

setlocal enabledelayedexpansion

echo ================================================
echo Casino Calendar - Complete Startup
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

REM Start the REST API in a new window
echo Starting REST API...
echo Command: !PYTHON_EXE! api/event_api.py
start "Casino Calendar - REST API" /D "!PROJECT_ROOT!" "!PYTHON_EXE!" api/event_api.py

REM Give the API a moment to start
echo Waiting for API to initialize...
timeout /t 2 /nobreak

REM Start the Dash application in a new window
echo Starting Dash Application...
echo Command: !PYTHON_EXE! app.py
start "Casino Calendar - Dash App" /D "!PROJECT_ROOT!" "!PYTHON_EXE!" app.py

echo.
echo ================================================
echo Services Started
echo ================================================
echo REST API:     http://localhost:5001
echo Dash App:     http://localhost:8050
echo.
echo Press any key to close this window...
pause >nul

endlocal
