@echo off
REM Casino Calendar - Quick Setup Launcher
REM Proxies to the Windows setup script in scripts\windows

for %%I in ("%~dp0.") do set "CC_ROOT_DIR=%%~fI"
set "CC_ENV_PATH=%CC_ROOT_DIR%\.env"
set "CC_LOG_SOURCE=root/setup.bat"
call :CC_RESOLVE_LOG_FILE "%CC_ENV_PATH%" "ROOT_SETUP_BAT_LOG_FILE" "logs\casino_calendar_batch_setup.log" "%CC_ROOT_DIR%"

call :CC_LOG INFO Running Casino Calendar Setup...
call "scripts\windows\setup.bat"
set "SETUP_EXIT=%ERRORLEVEL%"
if not "%SETUP_EXIT%"=="0" (
    call :CC_LOG ERROR Setup failed with exit code %SETUP_EXIT%.
    goto END_SETUP
)

set "ROOT_DIR=%~dp0"
set "ACTIVATE_CMD=%ROOT_DIR%.venv\Scripts\activate.bat"
set "ACTIVATE_PS=%ROOT_DIR%.venv\Scripts\Activate.ps1"
if not exist "%ACTIVATE_CMD%" goto SKIP_PROMPT

echo.
call :CC_LOG INFO Virtual environment options:
call :CC_LOG INFO "  [1] Activate this terminal session now"
call :CC_LOG INFO "  [2] Open a new CMD window with (.venv) active"
call :CC_LOG INFO "  [S] Skip activation (default)"
set "POST_CHOICE="
set /p POST_CHOICE=Select option [default S]: 
if not defined POST_CHOICE set "POST_CHOICE=S"
call set "POST_CHOICE=%%POST_CHOICE:~0,1%%"
if /I "%POST_CHOICE%"=="2" goto OPEN_NEW_WINDOW
if /I "%POST_CHOICE%"=="1" goto ACTIVATE_CURRENT

goto SKIP_PROMPT

:ACTIVATE_CURRENT
call :CC_LOG INFO Activating current terminal session...
call "%ACTIVATE_CMD%"
title Casino Calendar venv
set "SETUP_EXIT=0"
goto END_SETUP

:OPEN_NEW_WINDOW
call :CC_LOG INFO Launching a new CMD window with the venv activated...
start "Casino Calendar venv" cmd.exe /k ""%ACTIVATE_CMD%" & title Casino Calendar venv"
set "SETUP_EXIT=0"

echo.
call :CC_LOG INFO A new window should appear with (.venv) active.

goto SKIP_PROMPT

:SKIP_PROMPT
echo.
call :CC_LOG INFO To activate manually:
call :CC_LOG INFO "  CMD: call ""%ACTIVATE_CMD%"""
call :CC_LOG INFO "  PS:  %ACTIVATE_PS%"

:END_SETUP
exit /b %SETUP_EXIT%

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
