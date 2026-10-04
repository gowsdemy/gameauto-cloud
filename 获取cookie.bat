@echo off
chcp 65001 >nul
REM Launcher: all Chinese UI lives in get_cookie.ps1 (this file stays ASCII on purpose).
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0get_cookie.ps1"
endlocal
