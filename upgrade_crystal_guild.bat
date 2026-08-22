@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" upgrade_crystal_guild.py
) else (
  python upgrade_crystal_guild.py
)
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo Crystal Guild upgrade check completed successfully.
) else (
  echo Crystal Guild upgrade check failed with code %RC%.
)
pause
exit /b %RC%
