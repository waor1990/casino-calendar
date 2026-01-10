@echo off
REM Casino Calendar - Quick Run Launcher
REM Proxies to the main Windows runner script in scripts\windows

call "scripts\windows\run_direct.bat"
exit /b %ERRORLEVEL%
