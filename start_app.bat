@echo off
REM Properly activate virtual environment and start the app

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Checking Python and environment...
python --version
echo LOG_FILE environment variable: %LOG_FILE%

echo Starting Casino Calendar application...
python app.py

pause
