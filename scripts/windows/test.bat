@echo off
setlocal enableextensions
REM Casino Calendar - Windows Test Runner

for %%I in ("%~dp0\..\..") do set "CC_ROOT_DIR=%%~fI"
set "CC_ENV_PATH=%CC_ROOT_DIR%\.env"
set "CC_LOG_SOURCE=windows/test.bat"
call :CC_RESOLVE_LOG_FILE "%CC_ENV_PATH%" "WIN_TEST_BAT_LOG_FILE" "logs\casino_calendar_batch_test_windows.log" "%CC_ROOT_DIR%"

call :CC_LOG INFO Starting Casino Calendar Windows tests...

REM Navigate to project root (two levels above this script)
cd /d "%~dp0\..\.."

set "PYTHONPATH=%CD%\src;%CD%"
set "PYTHONNOUSERSITE=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

set "CC_ORIG_CODEPAGE="
for /f "tokens=2 delims=:" %%a in ('chcp') do set "CC_ORIG_CODEPAGE=%%a"
set "CC_ORIG_CODEPAGE=%CC_ORIG_CODEPAGE: =%"
set "CC_CODEPAGE_CHANGED=0"
if not "%CC_ORIG_CODEPAGE%"=="65001" (
    chcp 65001 >nul
    set "CC_CODEPAGE_CHANGED=1"
)

REM Prefer the local virtual environment if available
set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
    set "PATH=%CD%\.venv\Scripts;%PATH%"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" scripts\python\run_tests.py
set "EXIT_CODE=%ERRORLEVEL%"

if "%EXIT_CODE%"=="0" (
    call :CC_LOG INFO Tests completed successfully.
) else (
    call :CC_LOG ERROR Tests failed with exit code %EXIT_CODE%.
)

if "%CC_CODEPAGE_CHANGED%"=="1" (
    chcp %CC_ORIG_CODEPAGE% >nul
)

exit /b %EXIT_CODE%

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
