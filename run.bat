@echo off
REM Casino Calendar - Run Application
REM Activates virtual environment and starts the application

echo 🎰 Starting Casino Calendar Application
echo ====================================

REM Check if virtual environment exists
IF NOT EXIST .venv (
    echo Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo Activating virtual environment...
call .\.venv\Scripts\activate.bat

echo Checking Python environment...
python --version

echo Starting application...
python app.py

pause
