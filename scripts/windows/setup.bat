@echo off
setlocal enableextensions
REM Casino Calendar - Quick Setup Script
REM Sets up Python virtual environment and installs all dependencies

echo Casino Calendar - Setup Script
echo ================================

REM Resolve project root (parent of scripts directory) without changing CWD
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "SCRIPTS_DIR=%%~fI"
for %%I in ("%SCRIPTS_DIR%..") do set "ROOT_DIR=%%~fI"
echo Using project root: %ROOT_DIR%

REM Determine expected venv path
set "EXPECTED_VENV=%ROOT_DIR%\.venv"

REM If venv missing, create and skip stale checks
if not exist "%EXPECTED_VENV%\Scripts\python.exe" goto :CREATE_VENV

REM Stale venv checks
set "STALE_VENV=0"
"%EXPECTED_VENV%\Scripts\python.exe" -c "import sys;print('ok')" >nul 2>nul
if ERRORLEVEL 1 set "STALE_VENV=1"

REM Query Python for its sys.prefix to validate venv location
set "VENV_TMP_FILE=%ROOT_DIR%\.tmp_venvpath_%RANDOM%_%TIME:~6,2%%TIME:~3,2%%TIME:~0,2%.txt"
del /f /q "%VENV_TMP_FILE%" 2>nul
"%EXPECTED_VENV%\Scripts\python.exe" -c "import sys, pathlib; print(pathlib.Path(sys.prefix).resolve())" > "%VENV_TMP_FILE%" 2>nul
set "ACTUAL_VENV="
set /p ACTUAL_VENV=<"%VENV_TMP_FILE%"
del /f /q "%VENV_TMP_FILE%" 2>nul
if defined ACTUAL_VENV (
  if /I not "%ACTUAL_VENV%"=="%EXPECTED_VENV%" set "STALE_VENV=1"
)

if "%STALE_VENV%"=="1" (
  echo Detected a stale or moved virtual environment at:
  echo   %EXPECTED_VENV%
  if defined ACTUAL_VENV echo Actual VIRTUAL_ENV is: %ACTUAL_VENV%
  set /p RECREATE_VENV=Recreate the virtual environment now? ^(Y/N^): 
  set "ANS_RECREATE="
  call set "ANS_RECREATE=%%RECREATE_VENV:~0,1%%"
  if /I "%ANS_RECREATE%"=="Y" (
    echo Removing old virtual environment...
    rmdir /s /q "%EXPECTED_VENV%"
    if ERRORLEVEL 1 (
      echo Failed to remove .venv. Close processes locking it and try again.
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
  echo Failed to create virtual environment
  exit /b 1
)

:HAVE_VENV

REM Use venv Python/Pip directly without activating (more robust on Windows shells)
set "VENV_DIR=%EXPECTED_VENV%"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PIP_EXE=%VENV_DIR%\Scripts\pip.exe"
if not exist "%PYTHON_EXE%" (
    echo Could not find venv Python at %PYTHON_EXE%
    echo Falling back to system Python. Consider recreating the venv.
    set "PYTHON_EXE=python"
)

REM Force UTF-8 for Python output to avoid Windows console encoding issues
set PYTHONIOENCODING=utf-8

REM Install/Verify Python dependencies
IF NOT EXIST "%ROOT_DIR%\requirements.txt" (
    echo Warning: requirements.txt not found
    goto SkipPythonDeps
)

echo Checking Python dependencies against requirements.txt...
"%PYTHON_EXE%" -m pip install --upgrade pip
if %ERRORLEVEL% NEQ 0 (
    echo Failed to upgrade pip
    exit /b 1
)

del /f /q "%ROOT_DIR%\.tmp_requirements_diff.txt" 2>nul
"%PYTHON_EXE%" "%ROOT_DIR%\scripts\python\verify_requirements.py" > "%ROOT_DIR%\.tmp_requirements_diff.txt"
set "REQS_OUT_OF_SYNC=%ERRORLEVEL%"
set "REQS_OUT_OF_SYNC=%ERRORLEVEL%"

if not "%REQS_OUT_OF_SYNC%"=="0" (
    echo.
    echo The following packages do not match requirements.txt:
    type "%ROOT_DIR%\.tmp_requirements_diff.txt"
    echo.
    set "UPDATE_REQS="
    set "ANS_UPD="
    set /p UPDATE_REQS=Update environment to match requirements.txt now? ^(Y/N^)?
    call set "ANS_UPD=%%UPDATE_REQS:~0,1%%"
    if /I "%ANS_UPD%"=="Y" (
        echo Running dependency resolver dry-run to check for conflicts...
        "%PYTHON_EXE%" -m pip install --dry-run -r "%ROOT_DIR%\requirements.txt" > "%ROOT_DIR%\.tmp_pip_dry_run.log" 2>&1
        if %ERRORLEVEL% NEQ 0 (
            echo Dependency resolver found issues:
            type "%ROOT_DIR%\.tmp_pip_dry_run.log"
            del /f /q "%ROOT_DIR%\.tmp_pip_dry_run.log" 2>nul
            echo Resolve the reported conflicts before rerunning setup.
            del /f /q "%ROOT_DIR%\.tmp_requirements_diff.txt" 2>nul
            exit /b 1
        )
        del /f /q "%ROOT_DIR%\.tmp_pip_dry_run.log" 2>nul
        echo Installing Python dependencies to match requirements.txt...
        "%PYTHON_EXE%" -m pip install -r "%ROOT_DIR%\requirements.txt"
        if %ERRORLEVEL% NEQ 0 (
            echo Failed to install Python dependencies
            del /f /q "%ROOT_DIR%\.tmp_requirements_diff.txt" 2>nul
            exit /b 1
        )
    ) else (
        echo Skipping Python dependency installation at user request.
    )
) else (
    echo Python packages already match requirements.txt.
)

del /f /q "%ROOT_DIR%\.tmp_requirements_diff.txt" 2>nul

:SkipPythonDeps

REM Install Node dependencies (CSS build moved to run_direct.bat)
set "NODE_CLEAN_SCRIPT=%ROOT_DIR%\scripts\node\cleanup-node-modules.mjs"
set "NODE_PACKAGE_VALIDATOR=%ROOT_DIR%\scripts\node\verify-package-json.mjs"
where npm >nul 2>nul && (
    if exist "%NODE_PACKAGE_VALIDATOR%" (
        echo Validating package.json...
        node "%NODE_PACKAGE_VALIDATOR%" --quiet
        if ERRORLEVEL 1 (
            echo package.json validation failed. Resolve the issues above and rerun setup.
            exit /b 1
        )
    )
    if exist "%NODE_CLEAN_SCRIPT%" (
        echo Removing stale npm staging directories...
        node "%NODE_CLEAN_SCRIPT%"
        if ERRORLEVEL 1 (
            echo Failed to clean stale Node.js directories. Resolve the issues above and rerun setup.
            exit /b 1
        )
    )
    echo Installing Node.js dependencies...
    npm install
    if ERRORLEVEL 1 (
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
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install pre-commit hooks
        exit /b 1
    )
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
echo.
set "OPEN_VENV="
set "ANS_OPEN="
set /p OPEN_VENV=Open a new CMD window activated in the virtual environment now? ^(Y/N^): 
call set "ANS_OPEN=%%OPEN_VENV:~0,1%%"
if /I "%ANS_OPEN%"=="Y" (
    echo Launching a new CMD window with the venv activated...
    start "Casino Calendar venv" cmd.exe /k "%EXPECTED_VENV%\Scripts\activate.bat & title Casino Calendar venv"
    echo A new window should appear with (.venv) active.
) else (
    echo To activate manually:
    echo   CMD: call "%EXPECTED_VENV%\Scripts\activate.bat"
    echo   PS:  %ROOT_DIR%\.venv\Scripts\Activate.ps1
)
