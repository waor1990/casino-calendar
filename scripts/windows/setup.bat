@echo off
setlocal enableextensions enabledelayedexpansion
REM Casino Calendar - Quick Setup Script
REM Sets up Python virtual environment and installs all dependencies

REM Resolve project root (parent of scripts directory) without changing CWD
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%\..") do set "SCRIPTS_DIR=%%~fI"
for %%I in ("%SCRIPTS_DIR%\..") do set "ROOT_DIR=%%~fI"
set "CC_ROOT_DIR=%ROOT_DIR%"
set "CC_ENV_PATH=%CC_ROOT_DIR%\.env"
set "CC_LOG_SOURCE=windows/setup.bat"
call :CC_RESOLVE_LOG_FILE "%CC_ENV_PATH%" "WIN_SETUP_BAT_LOG_FILE" "logs\casino_calendar_batch_setup_windows.log" "%CC_ROOT_DIR%"

call :CC_LOG INFO Casino Calendar - Setup Script
call :CC_LOG INFO ================================
call :CC_LOG INFO Using project root: %ROOT_DIR%

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
  call :CC_LOG WARNING Detected a stale or moved virtual environment at:
  call :CC_LOG WARNING "  %EXPECTED_VENV%"
  if defined ACTUAL_VENV call :CC_LOG WARNING Actual VIRTUAL_ENV is: %ACTUAL_VENV%
  set /p RECREATE_VENV=Recreate the virtual environment now? ^(Y/N^): 
  set "ANS_RECREATE="
  call set "ANS_RECREATE=%%RECREATE_VENV:~0,1%%"
  if /I "!ANS_RECREATE!"=="Y" (
    call :CC_LOG INFO Removing old virtual environment...
    rmdir /s /q "%EXPECTED_VENV%"
    if ERRORLEVEL 1 (
      call :CC_LOG ERROR Failed to remove .venv. Close processes locking it and try again.
      exit /b 1
    )
    goto :CREATE_VENV
  )
)
goto :HAVE_VENV

:CREATE_VENV
call :CC_LOG INFO Creating Python virtual environment...
python -m venv "%EXPECTED_VENV%"
if ERRORLEVEL 1 (
  call :CC_LOG ERROR Failed to create virtual environment
  exit /b 1
)

:HAVE_VENV

REM Use venv Python/Pip directly without activating (more robust on Windows shells)
set "VENV_DIR=%EXPECTED_VENV%"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PIP_EXE=%VENV_DIR%\Scripts\pip.exe"
if not exist "%PYTHON_EXE%" (
    call :CC_LOG WARNING Could not find venv Python at %PYTHON_EXE%
    call :CC_LOG WARNING Falling back to system Python. Consider recreating the venv.
    set "PYTHON_EXE=python"
)

REM Force UTF-8 for Python output to avoid Windows console encoding issues
set PYTHONIOENCODING=utf-8

REM Install/Verify Python dependencies
IF NOT EXIST "%ROOT_DIR%\requirements.txt" (
    call :CC_LOG WARNING Warning: requirements.txt not found
    goto SkipPythonDeps
)

call :CC_LOG INFO Checking Python dependencies against requirements.txt...
"%PYTHON_EXE%" -m pip install --upgrade pip
if %ERRORLEVEL% NEQ 0 (
    call :CC_LOG ERROR Failed to upgrade pip
    exit /b 1
)

del /f /q "%ROOT_DIR%\.tmp_requirements_diff.txt" 2>nul
"%PYTHON_EXE%" "%ROOT_DIR%\scripts\python\verify_requirements.py" > "%ROOT_DIR%\.tmp_requirements_diff.txt"
set "REQS_OUT_OF_SYNC=%ERRORLEVEL%"
set "REQS_OUT_OF_SYNC=%ERRORLEVEL%"

if not "%REQS_OUT_OF_SYNC%"=="0" (
    echo.
    call :CC_LOG WARNING The following packages do not match requirements.txt:
    type "%ROOT_DIR%\.tmp_requirements_diff.txt"
    echo.
    set "UPDATE_REQS="
    set "ANS_UPD="
    set /p UPDATE_REQS=Update environment to match requirements.txt now? ^(Y/N^)?
    call set "ANS_UPD=%%UPDATE_REQS:~0,1%%"
    if /I "!ANS_UPD!"=="Y" (
        call :CC_LOG INFO Running dependency resolver dry-run to check for conflicts...
        "%PYTHON_EXE%" -m pip install --dry-run -r "%ROOT_DIR%\requirements.txt" > "%ROOT_DIR%\.tmp_pip_dry_run.log" 2>&1
        if !ERRORLEVEL! NEQ 0 (
            call :CC_LOG ERROR Dependency resolver found issues:
            type "%ROOT_DIR%\.tmp_pip_dry_run.log"
            del /f /q "%ROOT_DIR%\.tmp_pip_dry_run.log" 2>nul
            call :CC_LOG ERROR Resolve the reported conflicts before rerunning setup.
            del /f /q "%ROOT_DIR%\.tmp_requirements_diff.txt" 2>nul
            exit /b 1
        )
        del /f /q "%ROOT_DIR%\.tmp_pip_dry_run.log" 2>nul
        call :CC_LOG INFO Installing Python dependencies to match requirements.txt...
        "%PYTHON_EXE%" -m pip install -r "%ROOT_DIR%\requirements.txt"
        if !ERRORLEVEL! NEQ 0 (
            call :CC_LOG ERROR Failed to install Python dependencies
            del /f /q "%ROOT_DIR%\.tmp_requirements_diff.txt" 2>nul
            exit /b 1
        )
    ) else (
        call :CC_LOG INFO Skipping Python dependency installation at user request.
    )
) else (
    call :CC_LOG INFO Python packages already match requirements.txt.
)

del /f /q "%ROOT_DIR%\.tmp_requirements_diff.txt" 2>nul

:SkipPythonDeps

REM Install Node dependencies (CSS build moved to run_direct.bat)
set "NODE_CLEAN_SCRIPT=%ROOT_DIR%\scripts\node\cleanup-node-modules.mjs"
set "NODE_PACKAGE_VALIDATOR=%ROOT_DIR%\scripts\node\verify-package-json.mjs"
where npm >nul 2>nul && (
    if exist "%NODE_PACKAGE_VALIDATOR%" (
        call :CC_LOG INFO Validating package.json...
        node "%NODE_PACKAGE_VALIDATOR%" --quiet
        if ERRORLEVEL 1 (
            call :CC_LOG ERROR package.json validation failed. Resolve the issues above and rerun setup.
            exit /b 1
        )
    )
    if exist "%NODE_CLEAN_SCRIPT%" (
        call :CC_LOG INFO Removing stale npm staging directories...
        node "%NODE_CLEAN_SCRIPT%"
        if ERRORLEVEL 1 (
            call :CC_LOG ERROR Failed to clean stale Node.js directories. Resolve the issues above and rerun setup.
            exit /b 1
        )
    )
    call :CC_LOG INFO Installing Node.js dependencies...
    npm install
    if ERRORLEVEL 1 (
        call :CC_LOG ERROR Failed to install Node.js dependencies
        exit /b 1
    )
    call :CC_LOG INFO Node.js dependencies installed ^(CSS will be built when running the app^)
) || (
    call :CC_LOG WARNING Warning: npm not found, skipping Node.js dependencies
)

REM Install pre-commit hooks
where pre-commit >nul 2>nul && (
    call :CC_LOG INFO Installing pre-commit hooks...
    pre-commit install
    if !ERRORLEVEL! NEQ 0 (
        call :CC_LOG ERROR Failed to install pre-commit hooks
        exit /b 1
    )
) || (
    call :CC_LOG WARNING Warning: pre-commit not found, skipping hooks installation
)

echo.
call :CC_LOG INFO Setup completed successfully!
echo.
call :CC_LOG INFO To run the application (CSS will be built automatically):
call :CC_LOG INFO "  run_direct.bat"
call :CC_LOG INFO "  or use VSCode task: ""Run Casino Calendar App"""
echo.
call :CC_LOG INFO Note: CSS is now built automatically when running the app for convenience.
echo.
set "OPEN_VENV="
set "ANS_OPEN="
set /p OPEN_VENV=Open a new CMD window activated in the virtual environment now? ^(Y/N^): 
call set "ANS_OPEN=%%OPEN_VENV:~0,1%%"
if /I "%ANS_OPEN%"=="Y" (
    call :CC_LOG INFO Launching a new CMD window with the venv activated...
    start "Casino Calendar venv" cmd.exe /k "%EXPECTED_VENV%\Scripts\activate.bat & title Casino Calendar venv"
    call :CC_LOG INFO A new window should appear with (.venv) active.
) else (
    call :CC_LOG INFO To activate manually:
    call :CC_LOG INFO "  CMD: call ""%EXPECTED_VENV%\Scripts\activate.bat"""
    call :CC_LOG INFO "  PS:  %ROOT_DIR%\.venv\Scripts\Activate.ps1"
)
exit /b 0

:CC_READ_ENV
set "CC_ENV_PATH=%~1"
set "CC_ENV_KEY=%~2"
set "CC_ENV_VALUE="
if not exist "%CC_ENV_PATH%" exit /b 0
for /f "usebackq tokens=1,* delims== eol=#" %%A in ("%CC_ENV_PATH%") do (
    if /I "%%A"=="%CC_ENV_KEY%" set "CC_ENV_VALUE=%%B"
)
exit /b 0

:CC_RESOLVE_LOG_FILE
set "CC_ENV_PATH=%~1"
set "CC_ENV_KEY=%~2"
set "CC_DEFAULT_LOG=%~3"
set "CC_ROOT_DIR=%~4"
set "CC_ENV_VALUE="
call :CC_READ_ENV "%CC_ENV_PATH%" "%CC_ENV_KEY%"
if defined CC_ENV_VALUE (
    set "CC_LOG_FILE=%CC_ENV_VALUE%"
) else (
    set "CC_LOG_FILE=%CC_DEFAULT_LOG%"
)
set "CC_LOG_PATH=%CC_LOG_FILE%"
if "%CC_LOG_PATH:~0,2%"=="\\" goto CC_LOG_ABS
if "%CC_LOG_PATH:~1,1%"==":" goto CC_LOG_ABS
if "%CC_LOG_PATH:~0,1%"=="\\" goto CC_LOG_ABS
set "CC_LOG_PATH=%CC_ROOT_DIR%\%CC_LOG_PATH%"
:CC_LOG_ABS
set "CC_LOG_FILE=%CC_LOG_PATH%"
for %%I in ("%CC_LOG_FILE%") do set "CC_LOG_DIR=%%~dpI"
if not exist "%CC_LOG_DIR%" mkdir "%CC_LOG_DIR%" >nul 2>nul
exit /b 0

:CC_LOG_TIMESTAMP
for /f "usebackq delims=" %%A in (`powershell -NoProfile -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""` ) do (
    set "CC_LOG_TIMESTAMP=%%A"
)
exit /b 0

:CC_LOG
setlocal EnableDelayedExpansion
set "CC_LEVEL=%~1"
shift /1
set "CC_MESSAGE=%*"
if not defined CC_MESSAGE (
    echo.
    endlocal
    exit /b 0
)
if /I "!CC_LEVEL!"=="WARN" set "CC_LEVEL=WARNING"
call :CC_LOG_TIMESTAMP
set "CC_LOG_LINE=!CC_LOG_TIMESTAMP! | !CC_LEVEL! | !CC_LOG_SOURCE! | !CC_MESSAGE!"
echo !CC_MESSAGE!
>> "!CC_LOG_FILE!" echo !CC_LOG_LINE!
endlocal
exit /b 0
