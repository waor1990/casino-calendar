@echo off
echo ================================================
echo Casino Calendar - Development Environment Test
echo ================================================
echo.

echo [1/5] Checking virtual environment...
if exist ".venv\Scripts\python.exe" (
    echo ✓ Virtual environment found
) else (
    echo ✗ Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo.
echo [2/5] Testing Python and dependencies...
".venv\Scripts\python.exe" test_imports.py
if %errorlevel% neq 0 (
    echo ✗ Import test failed
    pause
    exit /b 1
)

echo.
echo [3/5] Checking data files...
if exist "data\casino_events.csv" (
    echo ✓ Data files found
) else (
    echo ✗ Data files missing
    pause
    exit /b 1
)

echo.
echo [4/5] Starting application...
echo Starting Casino Calendar in debug mode...
echo Application will be available at: http://localhost:8050
echo Press Ctrl+C to stop the application
echo.

".venv\Scripts\python.exe" app.py

echo.
echo [5/5] Application stopped.
pause
