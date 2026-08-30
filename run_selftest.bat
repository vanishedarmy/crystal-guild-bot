@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\activate (
  echo ERROR: Crystal Guild virtual environment is missing. Run setup_windows.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate
echo Running Crystal Guild v1.5.0 - Trails & Raids Alpha 2 bot integrity checks...
python -m compileall -q crystal_guild tests
if errorlevel 1 goto :failed
python -m unittest discover -s tests -v
if errorlevel 1 goto :failed
echo.
echo ALL CRYSTAL GUILD CHECKS PASSED.
pause
exit /b 0
:failed
echo.
echo CRYSTAL GUILD SELF-TEST FAILED. Review the output above and logs\crystal_guild.log if present.
pause
exit /b 1
