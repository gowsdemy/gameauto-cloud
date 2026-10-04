@echo off
chcp 65001 >nul
REM One-click: get the session cookie (runs locally, opens a real browser) and print the SESSION_COOKIES text
setlocal
cd /d "%~dp0"

REM check config.env
if exist config.env goto have_config
echo [ERROR] config.env not found.
echo   Copy config.env.example to config.env, then fill in USERNAME and PASSWORD.
echo   Example:  copy config.env.example config.env
pause
exit /b 1
:have_config

REM create venv if missing
if exist .venv\Scripts\python.exe goto have_venv
echo [STEP] Creating Python virtual environment...
py -3 -m venv .venv 2>nul
if exist .venv\Scripts\python.exe goto have_venv
python -m venv .venv 2>nul
if not exist .venv\Scripts\python.exe goto venv_fail
:have_venv
call .venv\Scripts\activate.bat
goto deps

:venv_fail
echo [ERROR] Could not create Python environment. Is Python installed and on PATH?
pause
exit /b 1

:deps
python -c "import ddddocr, playwright" 2>nul
if not errorlevel 1 goto run
echo [STEP] Installing dependencies, first time only...
python -m pip install --upgrade pip
pip install ddddocr playwright
:run

echo [STEP] Getting cookie ...
python get_cookie.py

echo.
echo [DONE] Press any key to close.
pause >nul
endlocal
