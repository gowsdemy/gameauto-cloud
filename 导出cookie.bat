@echo off
chcp 65001 >nul
REM Export local session cookie -> base64 text for the SESSION_COOKIES secret
setlocal
cd /d "%~dp0"
python export_cookie.py %*
echo.
pause
endlocal
