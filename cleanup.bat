@echo off
REM Casino Calendar - Log Cleanup Launcher
REM Proxies to the Windows log cleanup utility in scripts\windows

echo Starting Casino Calendar Log Cleanup...
call "scripts\windows\cleanup_logs.bat" %*
