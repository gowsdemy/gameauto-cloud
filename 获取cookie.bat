@echo off
chcp 65001 >nul
REM GameMale cloud - one-time local tool to get the session cookie.
REM All user prompts (Chinese) come from get_cookie.py; this file stays ASCII on purpose.
setlocal
cd /d "%~dp0"

py -3 --version >nul 2>nul
if not errorlevel 1 goto run_py3
python --version >nul 2>nul
if not errorlevel 1 goto run_py

echo [ERROR] Python not found. Please install Python 3.10+ and tick "Add Python to PATH".
echo         After installing, close this window and run this file again.
pause
exit /b 1

:run_py3
py -3 get_cookie.py
goto done

:run_py
python get_cookie.py

:done
echo.
pause
endlocal
