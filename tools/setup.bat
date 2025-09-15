@echo off
REM Casino Calendar - Quick Setup Script
REM Sets up Python virtual environment and installs all dependencies

echo Casino Calendar - Setup Script
echo ================================

REM Navigate to project root (parent of tools directory)
cd /d "%~dp0\.."

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

REM Force UTF-8 for Python output to avoid Windows console encoding issues
set PYTHONIOENCODING=utf-8

REM Install Python dependencies
IF EXIST requirements.txt (
    echo Installing Python dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install Python dependencies
        exit /b 1
    )
) else (
    echo Warning: requirements.txt not found
)

REM Install Node dependencies (CSS build moved to run_direct.bat)
where npm >nul 2>nul && (
    echo Installing Node.js dependencies...
    npm install 
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install Node.js dependencies
        exit /b 1
    )
    echo Node.js dependencies installed ^(CSS will be built when running the app^)
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
echo Setup completed successfully!
echo.
echo To run the application (CSS will be built automatically):
echo   run_direct.bat
echo   or use VSCode task: "Run Casino Calendar App"
echo.
echo Note: CSS is now built automatically when running the app for convenience.
