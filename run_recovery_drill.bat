@echo off
setlocal
cd /d "%~dp0"
python run_maintenance.py --recovery-drill
if errorlevel 1 (
  echo.
  echo CLOUD RUNTIME RECOVERY DRILL FAILED. The live database was not overwritten.
) else (
  echo.
  echo CLOUD RUNTIME RECOVERY DRILL PASSED. The live database was not modified.
)
pause
