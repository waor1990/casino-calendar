@echo off
setlocal enabledelayedexpansion

REM Resolve project root
for %%I in ("%~dp0\..\..") do set "ROOT_DIR=%%~fI"
cd /d "%ROOT_DIR%"

echo.
echo ================================================
echo Casino Calendar - Direct Application Runner
echo ================================================
echo.

REM Set environment variables
set "PYTHONPATH=%CD%\src;%CD%"
set "PYTHONNOUSERSITE=1"
set "PYTHONIOENCODING=utf-8"

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found at .venv\Scripts\python.exe
    echo Please run scripts\windows\setup.bat first
    pause
    exit /b 1
)

echo [OK] Virtual environment found
echo [OK] Python: %CD%\.venv\Scripts\python.exe
echo.

REM Build CSS if npm available
where npm >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Building CSS from SCSS...
    call npm run build:css
    if ERRORLEVEL 1 (
        echo WARNING: CSS build failed
        echo Continuing with existing CSS...
    )
) else (
    echo WARNING: npm not found, skipping CSS build
)

echo.
echo Launching application...
.venv\Scripts\python.exe app.py
exit /b %ERRORLEVEL%
