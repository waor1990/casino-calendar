@echo off
setlocal enabledelayedexpansion
REM Casino Calendar - Quick Setup Launcher
REM Proxies to the Windows setup script in scripts\windows

set "CC_ROOT_DIR=%~dp0"
set "CC_ENV_PATH=%CC_ROOT_DIR%.env"
set "CC_LOG_SOURCE=root/setup.bat"
call :CC_RESOLVE_LOG_FILE "%CC_ENV_PATH%" "ROOT_SETUP_BAT_LOG_FILE" "logs\casino_calendar_batch_setup.log" "%CC_ROOT_DIR%"

call :CC_LOG INFO Casino Calendar - Setup Script
call :CC_LOG INFO ================================

set "CC_SUPPRESS_SETUP_BANNER=1"
if defined CC_LOG_FILE (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%CC_ROOT_DIR%scripts\windows\tee_setup_output.ps1" -ScriptPath "%CC_ROOT_DIR%scripts\windows\setup.bat" -LogFile "%CC_LOG_FILE%" -LogSource "%CC_LOG_SOURCE%" -ProjectRoot "%CC_ROOT_DIR%"
) else (
    cmd /c "%CC_ROOT_DIR%scripts\windows\setup.bat"
)
set "SETUP_EXIT=%ERRORLEVEL%"

if not "%SETUP_EXIT%"=="0" (
    call :CC_LOG ERROR Setup failed with exit code %SETUP_EXIT%
    exit /b %SETUP_EXIT%
)

set "ROOT_DIR=%~dp0"
set "ACTIVATE_CMD=%ROOT_DIR%.venv\Scripts\activate.bat"

if not exist "%ACTIVATE_CMD%" (
    call :CC_LOG ERROR Virtual environment not found
    exit /b 1
)

call :CC_LOG INFO Virtual environment options:
call :CC_LOG INFO [1] Activate this terminal session now
call :CC_LOG INFO [2] Open a new CMD window with (.venv) active
call :CC_LOG INFO [S] Skip activation ^(default^)
set /p POST_CHOICE=Select option [default S]: 
if not defined POST_CHOICE set "POST_CHOICE=S"
call set "POST_CHOICE=%%POST_CHOICE:~0,1%%"

if /I "!POST_CHOICE!"=="1" (
    call :CC_LOG INFO Activating virtual environment in current terminal...
    endlocal & call "%~dp0.venv\Scripts\activate.bat" & title Casino Calendar venv
    goto :EOF
)

if /I "!POST_CHOICE!"=="2" (
    call :CC_LOG INFO Opening new CMD window with venv activated...
    start "Casino Calendar venv" cmd.exe /k "call "%ACTIVATE_CMD%" & title Casino Calendar venv"
    exit /b 0
)

call :CC_LOG INFO To activate manually:
call :CC_LOG INFO CMD: call "%ACTIVATE_CMD%"
call :CC_LOG INFO PS:  "%ROOT_DIR%.venv\Scripts\Activate.ps1"
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

:CC_LOG
setlocal EnableDelayedExpansion
set "CC_LEVEL=%~1"
set "CC_MESSAGE=%*"
if /I "!CC_LEVEL!"=="INFO" if /I "!CC_MESSAGE:~0,5!"=="INFO " set "CC_MESSAGE=!CC_MESSAGE:~5!"
if /I "!CC_LEVEL!"=="ERROR" if /I "!CC_MESSAGE:~0,6!"=="ERROR " set "CC_MESSAGE=!CC_MESSAGE:~6!"
if /I "!CC_LEVEL!"=="WARNING" if /I "!CC_MESSAGE:~0,8!"=="WARNING " set "CC_MESSAGE=!CC_MESSAGE:~8!"
if not defined CC_MESSAGE set "CC_MESSAGE="
if /I "!CC_LEVEL!"=="WARN" set "CC_LEVEL=WARNING"
if "!CC_MESSAGE!"=="" (
    >CON echo.
) else (
    >CON echo !CC_MESSAGE!
)
if defined CC_LOG_FILE (
    set "CC_LOG_LEVEL=!CC_LEVEL!"
    set "CC_LOG_MESSAGE=!CC_MESSAGE!"
    powershell -NoProfile -ExecutionPolicy Bypass -File "%CC_ROOT_DIR%scripts\windows\append_setup_log.ps1"
)
endlocal
exit /b 0
