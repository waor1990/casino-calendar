@echo off
REM Casino Calendar - Quick Setup Launcher
REM Proxies to the Windows setup script in scripts\windows

echo Running Casino Calendar Setup...
call "scripts\windows\setup.bat"
set "SETUP_EXIT=%ERRORLEVEL%"
if not "%SETUP_EXIT%"=="0" goto END_SETUP

set "ROOT_DIR=%~dp0"
set "ACTIVATE_CMD=%ROOT_DIR%.venv\Scripts\activate.bat"
set "ACTIVATE_PS=%ROOT_DIR%.venv\Scripts\Activate.ps1"
if not exist "%ACTIVATE_CMD%" goto SKIP_PROMPT

echo.
echo Virtual environment options:
echo   [1] Activate this terminal session now
echo   [2] Open a new CMD window with (.venv) active
echo   [S] Skip activation (default)
set "POST_CHOICE="
set /p POST_CHOICE=Select option [default S]:
if not defined POST_CHOICE set "POST_CHOICE=S"
call set "POST_CHOICE=%%POST_CHOICE:~0,1%%"
if /I "%POST_CHOICE%"=="2" goto OPEN_NEW_WINDOW
if /I "%POST_CHOICE%"=="1" goto ACTIVATE_CURRENT

goto SKIP_PROMPT

:ACTIVATE_CURRENT
echo Activating current terminal session...
call "%ACTIVATE_CMD%"
title Casino Calendar venv
set "SETUP_EXIT=0"
goto END_SETUP

:OPEN_NEW_WINDOW
echo Launching a new CMD window with the venv activated...
start "Casino Calendar venv" cmd.exe /k ""%ACTIVATE_CMD%" & title Casino Calendar venv"
set "SETUP_EXIT=0"

echo.
echo A new window should appear with (.venv) active.

goto SKIP_PROMPT

:SKIP_PROMPT
echo.
echo To activate manually:
echo   CMD: call "%ACTIVATE_CMD%"
echo   PS:  %ACTIVATE_PS%

:END_SETUP
exit /b %SETUP_EXIT%
