@echo off
REM Create a Windows scheduled task for log cleanup
REM Run this script as Administrator to create the scheduled task

echo Creating scheduled task for Casino Calendar log cleanup...

set PROJECT_PATH=%~dp0
set TASK_NAME="Casino Calendar Log Cleanup"
set PYTHON_SCRIPT="%PROJECT_PATH%scripts\cleanup_logs.py"
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

if %errorlevel% equ 0 (
    echo Scheduled task created successfully!
    echo Task will run every Sunday at 2:00 AM to clean up logs older than 30 days.
    echo.
    echo To view the task: schtasks /query /tn %TASK_NAME%
    echo To run manually: schtasks /run /tn %TASK_NAME%
    echo To delete task: schtasks /delete /tn %TASK_NAME% /f
) else (
    echo Failed to create scheduled task. Make sure you're running as Administrator.
)

echo.
pause
