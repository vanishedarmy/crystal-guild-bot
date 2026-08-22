@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\activate (
  echo ERROR: Run setup_windows.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate
python resolve_twitch_ids.py
set EXIT_CODE=%ERRORLEVEL%
echo.
if "%EXIT_CODE%"=="0" (
  echo Twitch IDs are ready.
) else (
  echo Twitch ID setup did not complete. See the message above.
)
pause
exit /b %EXIT_CODE%
