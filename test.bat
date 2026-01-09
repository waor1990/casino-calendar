@echo off
REM Casino Calendar - Quick Test Launcher
REM Proxies to the Windows test script in scripts\windows

for %%I in ("%~dp0.") do set "CC_ROOT_DIR=%%~fI"
set "CC_ENV_PATH=%CC_ROOT_DIR%\.env"
set "CC_LOG_SOURCE=root/test.bat"
call :CC_RESOLVE_LOG_FILE "%CC_ENV_PATH%" "ROOT_TEST_BAT_LOG_FILE" "logs\casino_calendar_batch_test.log" "%CC_ROOT_DIR%"

call :CC_LOG INFO Running Casino Calendar tests...
call "scripts\windows\test.bat"
set "CC_EXIT_CODE=%ERRORLEVEL%"
if "%CC_EXIT_CODE%"=="0" (
    call :CC_LOG INFO Tests completed successfully.
) else (
    call :CC_LOG ERROR Tests failed with exit code %CC_EXIT_CODE%.
)
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
