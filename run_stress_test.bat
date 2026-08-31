@echo off
setlocal
cd /d "%~dp0"
echo Running Crystal Guild v1.6.0 - Gold Saucer Alpha 4 synthetic release stress test...
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
