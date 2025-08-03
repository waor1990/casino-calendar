@echo off
REM Casino Calendar - Log Cleanup Launcher
REM Calls the log cleanup utility from tools directory

echo Starting Casino Calendar Log Cleanup...
call "tools\cleanup_logs.bat" %*
