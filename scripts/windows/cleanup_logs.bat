@echo off
REM Casino Calendar - Log Cleanup Utility
REM Cleans up old log files and provides log management options

echo Casino Calendar Log Cleanup Utility
echo =====================================

REM Navigate to project root (two levels above this script)
cd /d "%~dp0\..\.."

REM Check if virtual environment exists
IF NOT EXIST .venv (
    echo Virtual environment not found. Please run scripts\windows\setup.bat first.
    pause
    exit /b 1
)

echo Activating virtual environment...
call .\.venv\Scripts\activate.bat

echo.
:SELECTFILE
echo.
echo Select which log file to manage:
echo   [1] casino_calendar_prod.log
echo   [2] casino_calendar_maintenance.log
echo   [3] casino_calendar_http.log
echo   [4] All log files
echo   [5] Exit
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
    echo Invalid choice.
    goto SELECTFILE
)

:MENU
echo.
echo Managing: %TARGET_NAME%
echo Select how you want to archive the LOG_FILES:
echo   [2] Archive by month (keep only current month in active log)
echo   [3] Copy current log file into archive folder
echo   [4] Show log directory info
echo   [5] Custom days: copy-and-archive (enter days)
echo   [6] Exit
set /p CHOICE=Enter choice [2-6]: 

if "%CHOICE%"=="2" goto OPT2_BYMONTH
if "%CHOICE%"=="3" goto OPT3_COPY
if "%CHOICE%"=="4" goto OPT4_INFO
if "%CHOICE%"=="5" goto OPT5_CUSTOM
if "%CHOICE%"=="6" goto END

echo.
echo Invalid choice.
goto MENU

:OPT2_BYMONTH
echo Archiving prior months and keeping only current month in active log...
if defined MULTI_LOG (
    for %%L in (%TARGET_LOGS%) do (
        echo Processing %%~nxL...
        .\.venv\Scripts\python.exe scripts\python\cleanup_logs.py --archive-by-month --log-file "%%L"
    )
) else (
    .\.venv\Scripts\python.exe scripts\python\cleanup_logs.py --archive-by-month --log-file "%TARGET_LOG%"
)
goto DONE

:OPT3_COPY
echo Copying the current log file into the archive folder...
if defined MULTI_LOG (
    for %%L in (%TARGET_LOGS%) do (
        echo Processing %%~nxL...
        .\.venv\Scripts\python.exe scripts\python\cleanup_logs.py --copy-current --log-file "%%L"
    )
) else (
    .\.venv\Scripts\python.exe scripts\python\cleanup_logs.py --copy-current --log-file "%TARGET_LOG%"
)
goto DONE

:OPT4_INFO
echo Showing log directory information...
.\.venv\Scripts\python.exe scripts\python\cleanup_logs.py --info
goto DONE

:OPT5_CUSTOM
set /p DAYS=Enter number of days to copy to archive (e.g., 30): 
if "%DAYS%"=="" goto MENU
echo Copying lines older than %DAYS% day(s) into the archive...
if defined MULTI_LOG (
    for %%L in (%TARGET_LOGS%) do (
        echo Processing %%~nxL...
        .\.venv\Scripts\python.exe scripts\python\cleanup_logs.py --copy-split-days %DAYS% --log-file "%%L"
    )
) else (
    .\.venv\Scripts\python.exe scripts\python\cleanup_logs.py --copy-split-days %DAYS% --log-file "%TARGET_LOG%"
)
goto DONE

:DONE
echo.
echo Operation completed!
goto END

:END
echo.
echo Done.
echo.
echo Press any key to exit . . .
pause >nul
exit /b 0
