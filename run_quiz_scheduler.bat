@echo off
cd /d "%~dp0"
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

REM Load environment variables from .env file (simplified)
if exist .env (
    for /f "usebackq delims== tokens=1,2" %%a in (".env") do (
        if not "%%a"=="" if not "%%b"=="" if not "%%a"=="#" (
            set "%%a=%%b"
        )
    )
)

REM Create unique log filename
set "DATETIME=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%"
set "DATETIME=%DATETIME: =0%"
set "LOG_FILE=logs\quiz_bot_%DATETIME%.log"

REM Initialize log file
if not exist logs mkdir logs
echo ======================================== > "%LOG_FILE%"
echo Kanji Quiz Bot - Daily Execution >> "%LOG_FILE%"
echo Start Time: %date% %time% >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"

REM Step 1: Check virtual environment
echo [1/3] Checking virtual environment... >> "%LOG_FILE%"
if not exist new_venv\Scripts\python.exe (
    echo ERROR: Virtual environment not found >> "%LOG_FILE%"
    exit /b 1
)

REM Step 2: Run video creation (silent mode)
echo [2/3] Running video creation... >> "%LOG_FILE%"
new_venv\Scripts\python.exe core\app.py >> "%LOG_FILE%" 2>&1
set APP_EXIT=%ERRORLEVEL%

if %APP_EXIT% NEQ 0 (
    echo WARNING: Video creation failed with exit code %APP_EXIT% >> "%LOG_FILE%"
    echo Continuing with analysis anyway... >> "%LOG_FILE%"
) else (
    echo Video creation completed successfully >> "%LOG_FILE%"
)

REM Step 3: Run analysis and reporting (silent mode)
echo [3/3] Running analysis and reporting... >> "%LOG_FILE%"
new_venv\Scripts\python.exe core\reporter.py >> "%LOG_FILE%" 2>&1
set REPORT_EXIT=%ERRORLEVEL%

if %REPORT_EXIT% NEQ 0 (
    echo WARNING: Analysis failed with exit code %REPORT_EXIT% >> "%LOG_FILE%"
) else (
    echo Analysis completed successfully >> "%LOG_FILE%"
)

REM Final status
echo ======================================== >> "%LOG_FILE%"
echo End Time: %date% %time% >> "%LOG_FILE%"
if %APP_EXIT% EQU 0 if %REPORT_EXIT% EQU 0 (
    echo STATUS: All tasks completed successfully >> "%LOG_FILE%"
    set FINAL_EXIT=0
) else (
    echo STATUS: Some tasks completed with warnings - check log for details >> "%LOG_FILE%"
    set FINAL_EXIT=1
)
echo Log file: %LOG_FILE% >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"

exit /b %FINAL_EXIT%