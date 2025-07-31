@echo off
REM VSCode Terminal Environment Setup Script
REM This script fixes common terminal issues in VSCode

echo Setting up VSCode terminal environment...
echo.

REM Check if we're in the project directory
if not exist "app.py" (
    echo Error: Not in the Casino Calendar project directory
    echo Please run this script from the project root
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist ".venv" (
    echo Error: Virtual environment not found
    echo Please run setup.bat first to create the virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment and keep it active
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Add .venv\Scripts to PATH for this session
set PATH=%CD%\.venv\Scripts;%PATH%

REM Set up environment variables for this session
set PYTHONPATH=%CD%
set PROJECT_ROOT=%CD%

REM Verify Python is available
echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo Error: Python not working in virtual environment
    pause
    exit /b 1
)

echo.
echo ✓ Virtual environment activated
echo ✓ Python version: 
python --version
echo ✓ Project root: %CD%
echo ✓ Python path: %PYTHONPATH%
echo ✓ PATH updated with virtual environment

echo.
echo Environment setup complete!
echo You can now run Python commands and scripts.
echo.
echo Example commands:
echo   python app.py
echo   python scripts\cleanup_logs.py --info
echo   python -m pytest tests\
echo   pip install package-name
echo.
echo NOTE: This environment will persist for this terminal session only.
echo Close and reopen the terminal to reset to default environment.
