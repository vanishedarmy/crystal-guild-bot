@echo off
setlocal
cd /d "%~dp0"
echo Running Crystal Guild v1.1.14 - Cloud Continuity synthetic release stress test...
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
