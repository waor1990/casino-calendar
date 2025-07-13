@echo off
REM Create and activate venv if missing
IF NOT EXIST .venv (
    python -m venv .venv
)
call .\.venv\Scripts\activate.bat

REM Install Python dependencies
IF EXIST requirements.txt (
    pip install --upgrade pip
    pip install -r requirements.txt
)

REM Install Node dependencies & build CSS
where npm >nul 2>nul && (
    npm install 
    npm run build:css
)

REM Install pre-commit hooks
where pre-commit >nul 2>nul && (
    pre-commit install
)