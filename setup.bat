@echo off
REM Casino Calendar - Quick Setup Script
REM Sets up Python virtual environment and installs all dependencies

echo 🎰 Casino Calendar - Setup Script
echo ================================

REM Create and activate venv if missing
IF NOT EXIST .venv (
    echo Creating Python virtual environment...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment
        exit /b 1
    )
)

echo Activating virtual environment...
call .\.venv\Scripts\activate.bat

REM Install Python dependencies
IF EXIST requirements.txt (
    echo Installing Python dependencies...
    pip install --upgrade pip
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install Python dependencies
        exit /b 1
    )
) else (
    echo Warning: requirements.txt not found
)

REM Install Node dependencies & build CSS
where npm >nul 2>nul && (
    echo Installing Node.js dependencies...
    npm install 
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install Node.js dependencies
        exit /b 1
    )
    
    echo Building CSS...
    npm run build:css
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to build CSS
        exit /b 1
    )
) || (
    echo Warning: npm not found, skipping Node.js dependencies
)

REM Install pre-commit hooks
where pre-commit >nul 2>nul && (
    echo Installing pre-commit hooks...
    pre-commit install
) || (
    echo Warning: pre-commit not found, skipping hooks installation
)

echo.
echo ✅ Setup completed successfully!
echo.
echo To run the application:
echo   scripts\run.bat
echo.
echo To run in development mode with CSS watching:
echo   scripts\dev.bat
