@echo off
REM Casino Calendar - Log Cleanup Utility
REM Cleans up old log files and provides log management options

for %%I in ("%~dp0\..\..") do set "CC_ROOT_DIR=%%~fI"
set "CC_ENV_PATH=%CC_ROOT_DIR%\.env"
set "CC_LOG_SOURCE=windows/cleanup_logs.bat"
call :CC_RESOLVE_LOG_FILE "%CC_ENV_PATH%" "WIN_CLEANUP_LOGS_BAT_LOG_FILE" "logs\casino_calendar_batch_cleanup_logs.log" "%CC_ROOT_DIR%"

call :CC_LOG INFO Casino Calendar Log Cleanup Utility
call :CC_LOG INFO =====================================

REM Navigate to project root (two levels above this script)
cd /d "%CC_ROOT_DIR%"

REM Check if virtual environment exists
IF NOT EXIST .venv (
    call :CC_LOG ERROR Virtual environment not found. Please run scripts\windows\setup.bat first.
    pause
    exit /b 1
)

call :CC_LOG INFO Activating virtual environment...
call .\.venv\Scripts\activate.bat

echo.
:SELECTFILE
echo.
call :CC_LOG INFO Select which log file to manage:
call :CC_LOG INFO "  [1] casino_calendar_prod.log"
call :CC_LOG INFO "  [2] casino_calendar_maintenance.log"
call :CC_LOG INFO "  [3] casino_calendar_http.log"
call :CC_LOG INFO "  [4] All log files"
call :CC_LOG INFO "  [5] Exit"
set /p LOGCHOICE=Enter choice [1-5]: 

if "%LOGCHOICE%"=="1" (
    set "TARGET_LOG=logs\casino_calendar_prod.log"
    set "TARGET_NAME=casino_calendar_prod.log"
    set "MULTI_LOG="
) else if "%LOGCHOICE%"=="2" (
    set "TARGET_LOG=logs\casino_calendar_maintenance.log"
    set "TARGET_NAME=casino_calendar_maintenance.log"
    set "MULTI_LOG="
) else if "%LOGCHOICE%"=="3" (
    set "TARGET_LOG=logs\casino_calendar_http.log"
    set "TARGET_NAME=casino_calendar_http.log"
) else if "%LOGCHOICE%"=="4" (
    set "TARGET_LOGS=logs\casino_calendar_prod.log logs\casino_calendar_maintenance.log logs\casino_calendar_http.log"
    set "TARGET_NAME=all log files"
    set "MULTI_LOG=1"
) else if "%LOGCHOICE%"=="5" (
    goto END
) else (
    echo.
    call :CC_LOG WARNING Invalid choice.
    goto SELECTFILE
)

:MENU
echo.
call :CC_LOG INFO Managing: %TARGET_NAME%
call :CC_LOG INFO Select how you want to archive the LOG_FILES:
call :CC_LOG INFO "  [2] Archive by month (keep only current month in active log)"
call :CC_LOG INFO "  [3] Copy current log file into archive folder"
call :CC_LOG INFO "  [4] Show log directory info"
call :CC_LOG INFO "  [5] Custom days: copy-and-archive (enter days)"
call :CC_LOG INFO "  [6] Exit"
set /p CHOICE=Enter choice [2-6]: 

if "%CHOICE%"=="2" goto OPT2_BYMONTH
if "%CHOICE%"=="3" goto OPT3_COPY
if "%CHOICE%"=="4" goto OPT4_INFO
if "%CHOICE%"=="5" goto OPT5_CUSTOM
if "%CHOICE%"=="6" goto END

echo.
call :CC_LOG WARNING Invalid choice.
goto MENU

:OPT2_BYMONTH
call :CC_LOG INFO Archiving prior months and keeping only current month in active log...
if defined MULTI_LOG (
    for %%L in (%TARGET_LOGS%) do (
        call :CC_LOG INFO Processing %%~nxL...
        .\.venv\Scripts\python.exe scripts\python\cleanup_logs.py --archive-by-month --log-file "%%L"
    )
) else (
    .\.venv\Scripts\python.exe scripts\python\cleanup_logs.py --archive-by-month --log-file "%TARGET_LOG%"
)
goto DONE

:OPT3_COPY
call :CC_LOG INFO Copying the current log file into the archive folder...
if defined MULTI_LOG (
    for %%L in (%TARGET_LOGS%) do (
        call :CC_LOG INFO Processing %%~nxL...
        .\.venv\Scripts\python.exe scripts\python\cleanup_logs.py --copy-current --log-file "%%L"
    )
) else (
    .\.venv\Scripts\python.exe scripts\python\cleanup_logs.py --copy-current --log-file "%TARGET_LOG%"
)
goto DONE

:OPT4_INFO
call :CC_LOG INFO Showing log directory information...
.\.venv\Scripts\python.exe scripts\python\cleanup_logs.py --info
goto DONE

:OPT5_CUSTOM
set /p DAYS=Enter number of days to copy to archive (e.g., 30): 
if "%DAYS%"=="" goto MENU
call :CC_LOG INFO Copying lines older than %DAYS% day(s) into the archive...
if defined MULTI_LOG (
    for %%L in (%TARGET_LOGS%) do (
        call :CC_LOG INFO Processing %%~nxL...
        .\.venv\Scripts\python.exe scripts\python\cleanup_logs.py --copy-split-days %DAYS% --log-file "%%L"
    )
) else (
    .\.venv\Scripts\python.exe scripts\python\cleanup_logs.py --copy-split-days %DAYS% --log-file "%TARGET_LOG%"
)
goto DONE

:DONE
echo.
call :CC_LOG INFO Operation completed!
goto END

:END
echo.
call :CC_LOG INFO Done.
echo.
call :CC_LOG INFO Press any key to exit . . .
pause >nul
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
