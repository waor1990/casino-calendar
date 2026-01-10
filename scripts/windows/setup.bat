@echo off
setlocal enableextensions enabledelayedexpansion
REM Casino Calendar - Setup Script
REM Sets up Python virtual environment and installs all dependencies

REM Resolve project root
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%\..") do set "SCRIPTS_DIR=%%~fI"
for %%I in ("%SCRIPTS_DIR%\..") do set "ROOT_DIR=%%~fI"

if not defined CC_SUPPRESS_SETUP_BANNER (
  echo Casino Calendar - Setup Script
  echo ================================
)
echo Using project root: %ROOT_DIR%
echo.

REM Determine expected venv path
set "EXPECTED_VENV=%ROOT_DIR%\.venv"

REM If venv missing, create and skip stale checks
if not exist "%EXPECTED_VENV%\Scripts\python.exe" goto :CREATE_VENV

REM Stale venv checks
set "STALE_VENV=0"
"%EXPECTED_VENV%\Scripts\python.exe" -c "import sys;print('ok')" >nul 2>nul
if ERRORLEVEL 1 set "STALE_VENV=1"

if "%STALE_VENV%"=="1" (
  echo WARNING: Detected a stale or moved virtual environment
  set /p RECREATE_VENV="Recreate it now? (Y/N): "
  if /I "!RECREATE_VENV:~0,1!"=="Y" (
    echo Removing old virtual environment...
    rmdir /s /q "%EXPECTED_VENV%"
    if ERRORLEVEL 1 (
      echo ERROR: Failed to remove .venv
      exit /b 1
    )
    goto :CREATE_VENV
  )
)
goto :HAVE_VENV

:CREATE_VENV
echo Creating Python virtual environment...
python -m venv "%EXPECTED_VENV%"
if ERRORLEVEL 1 (
  echo ERROR: Failed to create virtual environment
  exit /b 1
)

:HAVE_VENV
set "PYTHON_EXE=%EXPECTED_VENV%\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    echo ERROR: Could not find Python at %PYTHON_EXE%
    exit /b 1
)

set PYTHONIOENCODING=utf-8

REM Install Python dependencies
if not exist "%ROOT_DIR%\requirements.txt" (
    echo WARNING: requirements.txt not found
    goto SkipPythonDeps
)

echo.
echo Checking Python dependencies...
"%PYTHON_EXE%" -m pip install --upgrade pip --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to upgrade pip
    exit /b 1
)

"%PYTHON_EXE%" "%ROOT_DIR%\scripts\python\verify_requirements.py" > "%ROOT_DIR%\.tmp_requirements_diff.txt" 2>&1
if ERRORLEVEL 1 (
    echo WARNING: Some packages do not match requirements.txt
    type "%ROOT_DIR%\.tmp_requirements_diff.txt"
    echo.
    set /p UPDATE_REQS="Install/update dependencies? (Y/N): "
    if /I "!UPDATE_REQS:~0,1!"=="Y" (
        echo Installing dependencies...
        "%PYTHON_EXE%" -m pip install -r "%ROOT_DIR%\requirements.txt"
        if ERRORLEVEL 1 (
            echo ERROR: Failed to install dependencies
            del /f /q "%ROOT_DIR%\.tmp_requirements_diff.txt" 2>nul
            exit /b 1
        )
    )
) else (
    echo INFO: All Python packages match requirements.txt
)

del /f /q "%ROOT_DIR%\.tmp_requirements_diff.txt" 2>nul

:SkipPythonDeps

REM Install Node dependencies
echo.
where npm >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Installing Node.js dependencies...
    npm install
    if ERRORLEVEL 1 (
        echo ERROR: Failed to install Node.js dependencies
        exit /b 1
    )
) else (
    echo WARNING: npm not found, skipping Node.js setup
)

echo.
echo Setup completed successfully!
echo.
set /p OPEN_VENV="Open new CMD with venv? (Y/N): "
if /I "!OPEN_VENV:~0,1!"=="Y" (
    start "Casino Calendar venv" cmd.exe /k "%EXPECTED_VENV%\Scripts\activate.bat & title Casino Calendar venv"
)
exit /b 0
