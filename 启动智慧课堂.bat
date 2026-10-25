@echo off
setlocal
cd /d "%~dp0"
title Start Intelligent Classroom

echo ============================================================
echo   Intelligent Classroom - starting, please wait...
echo ============================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"

echo.
echo ============================================================
echo   Finished. This window stays open - press any key to close.
echo   If something failed, check the messages above
echo   or open the log file: startup.log
echo ============================================================
pause >nul
