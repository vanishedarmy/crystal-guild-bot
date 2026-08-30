@echo off
setlocal
cd /d "%~dp0"
python run_maintenance.py --backup
if errorlevel 1 (
  echo.
  echo Backup was not completed. Review the message above.
) else (
  echo.
  echo Verified backup complete.
)
pause
