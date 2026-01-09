@echo off
REM Create a Windows scheduled task for log cleanup
REM Run this script as Administrator to create the scheduled task

for %%I in ("%~dp0\..\..") do set "CC_ROOT_DIR=%%~fI"
set "CC_ENV_PATH=%CC_ROOT_DIR%\.env"
set "CC_LOG_SOURCE=windows/create_scheduled_cleanup.bat"
call :CC_RESOLVE_LOG_FILE "%CC_ENV_PATH%" "WIN_CREATE_SCHEDULED_CLEANUP_BAT_LOG_FILE" "logs\casino_calendar_batch_scheduled_cleanup.log" "%CC_ROOT_DIR%"

call :CC_LOG INFO Creating scheduled task for Casino Calendar log cleanup...

set PROJECT_PATH=%~dp0..\..\
set TASK_NAME="Casino Calendar Log Cleanup"
set PYTHON_SCRIPT="%PROJECT_PATH%scripts\python\cleanup_logs.py"
set PYTHON_EXE="%PROJECT_PATH%.venv\Scripts\python.exe"

REM Create the task to run every Sunday at 2:00 AM
schtasks /create ^
    /tn %TASK_NAME% ^
    /tr "%PYTHON_EXE% %PYTHON_SCRIPT% --days 30 --quiet" ^
    /sc weekly ^
    /d SUN ^
    /st 02:00 ^
    /f ^
    /rl highest

set "CC_EXIT_CODE=%ERRORLEVEL%"
if "%CC_EXIT_CODE%"=="0" (
    call :CC_LOG INFO Scheduled task created successfully!
    call :CC_LOG INFO Task will run every Sunday at 2:00 AM to clean up logs older than 30 days.
    echo.
    call :CC_LOG INFO To view the task: schtasks /query /tn %TASK_NAME%
    call :CC_LOG INFO To run manually: schtasks /run /tn %TASK_NAME%
    call :CC_LOG INFO To delete task: schtasks /delete /tn %TASK_NAME% /f
) else (
    call :CC_LOG ERROR Failed to create scheduled task. Make sure you're running as Administrator.
)

echo.
pause
exit /b %CC_EXIT_CODE%

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
