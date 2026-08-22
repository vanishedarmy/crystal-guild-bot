@echo off
setlocal
cd /d "%~dp0"
python run_maintenance.py
if errorlevel 1 (
  echo.
  echo Cloud Runtime release-readiness check reported a problem.
) else (
  echo.
  echo Cloud Runtime release-readiness check passed.
)
pause
