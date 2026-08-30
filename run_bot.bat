@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\activate (
  echo ERROR: Crystal Guild virtual environment is missing.
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate
python run_bot.py
set EXIT_CODE=%ERRORLEVEL%
if not "%EXIT_CODE%"=="0" echo Crystal Guild exited with code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
