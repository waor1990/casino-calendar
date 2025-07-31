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

echo [OK] Virtual environment found
echo [OK] Python executable: %CD%\.venv\Scripts\python.exe
echo [OK] Environment variables set
echo.

REM Build CSS if npm is available
echo Building CSS from SCSS...
where npm >nul 2>nul
if !ERRORLEVEL! equ 0 (
    echo [INFO] npm found, attempting CSS build...
    npm run build:css
    set CSS_BUILD_RESULT=!ERRORLEVEL!
    if !CSS_BUILD_RESULT! equ 0 (
        echo [OK] CSS built successfully
    ) else (
        echo WARNING: CSS build failed with exit code !CSS_BUILD_RESULT!
        echo This might be due to:
        echo   - Missing Node.js dependencies: try 'npm install'
        echo   - SCSS syntax errors in assets/style.scss
        echo   - Missing assets directory or files
        echo Continuing with existing CSS files...
    )
) else (
    echo WARNING: npm not found, skipping CSS build
    echo Install Node.js and run 'npm install' to enable CSS building
)

REM Check if CSS file exists
if exist "assets\style.css" (
    echo [INFO] CSS file found: assets\style.css
) else (
    echo [WARN] CSS file not found: assets\style.css
    echo The application may not display correctly without CSS
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
    echo [ERROR] There was an error running the application.
    echo Check the logs in the logs/ directory for more information.
) else (
    echo [OK] Application stopped successfully.
)
echo ================================================
