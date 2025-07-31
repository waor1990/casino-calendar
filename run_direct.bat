@echo off
setlocal enabledelayedexpansion

echo ================================================
echo Casino Calendar - Direct Application Runner
echo ================================================
echo Working directory: %CD%
echo.

REM Navigate to script directory
cd /d "%~dp0"

REM Set environment variables
set PYTHONPATH=%CD%

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found at .venv\Scripts\python.exe
    echo Please run setup.bat first to create the virtual environment
    pause
    exit /b 1
)

echo ✓ Virtual environment found
echo ✓ Python executable: %CD%\.venv\Scripts\python.exe
echo ✓ Environment variables set
echo.

REM Build CSS if npm is available
echo Building CSS from SCSS...
where npm >nul 2>nul
if !ERRORLEVEL! equ 0 (
    npm run build:css
    if !ERRORLEVEL! equ 0 (
        echo ✓ CSS built successfully
    ) else (
        echo WARNING: CSS build failed, continuing with existing CSS
        echo Check that Node.js dependencies are installed: npm install
    )
) else (
    echo WARNING: npm not found, skipping CSS build
)
echo.

REM Run the application
echo Starting Casino Calendar application...
echo Application will be available at: http://localhost:8050
echo Press Ctrl+C to stop the application
echo.
echo Executing: "%CD%\.venv\Scripts\python.exe" app.py
echo ================================================
echo.

"%CD%\.venv\Scripts\python.exe" app.py

echo.
echo ================================================
echo Application finished with exit code: !ERRORLEVEL!
if !ERRORLEVEL! neq 0 (
    echo ✗ There was an error running the application.
    echo Check the logs in the logs/ directory for more information.
) else (
    echo ✓ Application stopped successfully.
)
echo ================================================
