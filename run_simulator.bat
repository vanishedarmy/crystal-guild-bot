@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\activate (
  echo ERROR: Crystal Guild virtual environment is missing. Run setup_windows.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate
python run_simulator.py
pause
