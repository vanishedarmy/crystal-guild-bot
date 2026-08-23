@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: Crystal Guild virtual environment is missing. Run setup_windows.bat first.
  pause
  exit /b 1
)

echo ============================================================
echo      CRYSTAL GUILD v1.1.14 - CLOUD TOKEN AUTH SESSION - HOTFIX 2
echo ============================================================
echo.
echo This temporary LOCAL session stores Twitch OAuth credentials in:
echo   %~dp0twitch_tokens.db
echo.
echo It does not enable Render/cloud mode and does not move your player DB.
echo Stop any other Crystal Guild Bot first so kupo_intern is not connected twice.
echo.
echo After the bot starts, use open_twitch_authorization.bat and authorize BOTH:
echo   1. dedicated bot account
echo   2. broadcaster / owner account
echo.
echo When both are authorized, press Ctrl+C once in this window and allow a clean shutdown.
echo Then run:
echo   python prepare_render_migration.py --token-db twitch_tokens.db
echo.
pause

set "CRYSTAL_GUILD_RUNTIME_MODE=local"
set "TWITCH_TOKEN_DB=%~dp0twitch_tokens.db"
".venv\Scripts\python.exe" run_bot.py
set EXIT_CODE=%ERRORLEVEL%
echo.
echo Token authorization session ended with code %EXIT_CODE%.
echo If authorization succeeded, twitch_tokens.db is ready for the migration helper.
pause
exit /b %EXIT_CODE%
