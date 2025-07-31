@echo off
REM Casino Calendar - Development Mode
REM Runs the app with CSS watching enabled

echo 🎰 Casino Calendar - Development Mode
echo ==================================

REM Check if virtual environment exists
IF NOT EXIST .venv (
    echo Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo Activating virtual environment...
call .\.venv\Scripts\activate.bat

REM Start CSS watching in background
where npm >nul 2>nul && (
    echo Starting CSS watcher...
    start /B npm run watch:css
) || (
    echo Warning: npm not found, CSS watching disabled
)

echo Starting application in development mode...
set LOG_LEVEL=DEBUG
python app.py

pause
