@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [SSRC Dashboard] First run setup...
    py -3 -m venv .venv
    if errorlevel 1 goto :error

    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    if errorlevel 1 goto :error

    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)

echo [SSRC Dashboard] Starting...
".venv\Scripts\python.exe" main.py

if errorlevel 1 goto :error
exit /b 0

:error
echo.
echo [SSRC Dashboard] Failed to start.
echo Check the messages above for details.
pause
exit /b 1
