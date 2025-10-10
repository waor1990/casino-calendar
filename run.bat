@echo off
REM Casino Calendar - Quick Run Launcher
REM Ensures CSS assets are built before delegating to the Windows runner

setlocal enabledelayedexpansion

REM Ensure commands execute from the repository root
cd /d "%~dp0"

echo ================================================
echo Casino Calendar - Quick Run Launcher
echo ================================================
echo [INFO] Checking front-end assets...

where npm >nul 2>nul
if !ERRORLEVEL! equ 0 (
    echo [DEBUG] npm detected - building CSS from SCSS sources
    call npm run build:css
    if !ERRORLEVEL! equ 0 (
        echo [OK] CSS assets built successfully
    ) else (
        echo [WARN] CSS build failed. The existing CSS will be used.
    )
) else (
    echo [WARN] npm not found - skipping CSS build. Install Node.js to enable asset builds.
)

echo.
echo [INFO] Launching Casino Calendar application...
call "scripts\windows\run_direct.bat"

endlocal
