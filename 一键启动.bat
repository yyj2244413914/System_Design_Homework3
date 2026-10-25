@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
if errorlevel 1 (
    echo.
    echo [ERROR] startup failed, run manually:
    echo         cd backend
    echo         python app.py
    pause
)
