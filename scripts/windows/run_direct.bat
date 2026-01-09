@echo off
setlocal enabledelayedexpansion

for %%I in ("%~dp0\..\..") do set "CC_ROOT_DIR=%%~fI"
set "CC_ENV_PATH=%CC_ROOT_DIR%\.env"
set "CC_LOG_SOURCE=windows/run_direct.bat"
call :CC_RESOLVE_LOG_FILE "%CC_ENV_PATH%" "WIN_RUN_DIRECT_BAT_LOG_FILE" "logs\casino_calendar_batch_run_direct.log" "%CC_ROOT_DIR%"

call :CC_LOG INFO ================================================
call :CC_LOG INFO Casino Calendar - Direct Application Runner
call :CC_LOG INFO ================================================
call :CC_LOG INFO Working directory: %CD%
echo.

REM Navigate to project root (two levels above this script)
cd /d "%CC_ROOT_DIR%"

REM Set environment variables (isolate from any pre-set PYTHONPATH)
set "PYTHONPATH=%CD%\src;%CD%"
set "PYTHONNOUSERSITE=1"
set "PYTHONIOENCODING=utf-8"

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    call :CC_LOG ERROR ERROR: Virtual environment not found at .venv\Scripts\python.exe
    call :CC_LOG ERROR Please run scripts\windows\setup.bat first to create the virtual environment
    pause
    exit /b 1
)

call :CC_LOG INFO [OK] Virtual environment found
call :CC_LOG INFO [OK] Python executable: %CD%\.venv\Scripts\python.exe
call :CC_LOG INFO [OK] Environment variables set (UTF-8 console enabled)
echo.

REM Build CSS if npm is available
call :CC_LOG INFO Building CSS from SCSS...
where npm >nul 2>nul
if !ERRORLEVEL! equ 0 (
    call :CC_LOG INFO [INFO] npm found, attempting CSS build...
    call :CC_LOG DEBUG [DEBUG] Running: npm run build:css
    call npm run build:css
    if !ERRORLEVEL! equ 0 (
        call :CC_LOG INFO [OK] CSS built successfully
    ) else (
        call :CC_LOG WARNING WARNING: CSS build failed
        call :CC_LOG WARNING This might be due to:
        call :CC_LOG WARNING "  - SCSS syntax errors in assets/styles/index.scss or imported files"
        call :CC_LOG WARNING "  - Missing Node.js dependencies: try 'npm install'"
        call :CC_LOG WARNING "  - Sass compiler version compatibility issues"
        call :CC_LOG WARNING "  - File permission problems"
        call :CC_LOG WARNING Continuing with existing CSS files...
    )
) else (
    call :CC_LOG WARNING WARNING: npm not found, skipping CSS build
    call :CC_LOG WARNING Install Node.js and run 'npm install' to enable CSS building
)

REM Check if CSS file exists
if exist "assets\dist\style.css" (
    call :CC_LOG INFO [INFO] CSS file found: assets\dist\style.css
) else (
    call :CC_LOG WARNING [WARN] CSS file not found: assets\dist\style.css
    call :CC_LOG WARNING The application may not display correctly without CSS
)
echo.
call :CC_LOG DEBUG [DEBUG] CSS build section completed, proceeding to run application...

REM Run the application
call :CC_LOG INFO Starting Casino Calendar application...
call :CC_LOG INFO Application will be available at: http://localhost:8050
call :CC_LOG INFO Press Ctrl+C to stop the application
echo.
call :CC_LOG DEBUG Executing: "%CD%\.venv\Scripts\python.exe" app.py
call :CC_LOG INFO ================================================
echo.
call :CC_LOG INFO ================================================
echo.

"%CD%\.venv\Scripts\python.exe" app.py

echo.
call :CC_LOG INFO ================================================
set "CC_EXIT_CODE=!ERRORLEVEL!"
call :CC_LOG INFO Application finished with exit code: !CC_EXIT_CODE!
if !CC_EXIT_CODE! neq 0 (
    call :CC_LOG ERROR [ERROR] There was an error running the application.
    call :CC_LOG ERROR Check the logs in the logs/ directory for more information.
) else (
    call :CC_LOG INFO [OK] Application stopped successfully.
)
call :CC_LOG INFO ================================================
exit /b !CC_EXIT_CODE!

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
