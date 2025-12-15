@echo off
REM Auto-activation script for VSCode terminals
REM This script automatically sets up the environment when opening a new terminal

REM Check if we're in the Casino Calendar project directory
if exist "app.py" if exist ".venv" (
    echo [Auto] Activating Casino Calendar environment...

    REM Activate virtual environment
    call .venv\Scripts\activate.bat >nul 2>&1

    REM Add .venv\Scripts to PATH
    set PATH=%CD%\.venv\Scripts;%PATH%

    REM Set environment variables
    set PYTHONPATH=%CD%
    set PROJECT_ROOT=%CD%

    echo [Auto] ✓ Environment ready - Python available
    echo [Auto] Use 'python app.py' to run the application
    echo.
) else (
    echo [Auto] Not in Casino Calendar project directory or .venv not found
    echo [Auto] Run 'setup_terminal.bat' to configure environment
    echo.
)
