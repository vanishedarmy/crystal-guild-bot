@echo off
setlocal
cd /d "%~dp0"
echo Running Crystal Guild v1.9.0 Alpha 2 - Economy Balance synthetic release stress test...
python run_stress_test.py %*
if errorlevel 1 (
  echo.
  echo CLOUD RUNTIME STRESS TEST FAILED.
  pause
  exit /b 1
)
echo.
echo CLOUD RUNTIME STRESS TEST PASSED.
pause
