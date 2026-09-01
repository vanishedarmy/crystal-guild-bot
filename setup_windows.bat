@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo   Crystal Guild v1.7.0 - Retainer Service Alpha 1 Setup
echo ========================================
echo.
echo Upgrading? Stop the old bot and preserve .env, crystal_guild.db, and .tio.tokens.json before replacing program files.
echo Omit the database if you want a fresh Guild.
echo.

if not exist .venv (
  echo Creating Python virtual environment...
  py -3 -m venv .venv 2>nul
  if errorlevel 1 python -m venv .venv
)

if not exist .venv\Scripts\activate (
  echo.
  echo ERROR: Could not create .venv. Install Python 3.11 or newer and try again.
  pause
  exit /b 1
)

call .venv\Scripts\activate
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 (
  echo.
  echo ERROR: Crystal Guild requires Python 3.11 or newer.
  echo Download Python: https://www.python.org/downloads/windows/
  python --version
  pause
  exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 goto :install_error
python -m pip install -r requirements.txt
if errorlevel 1 goto :install_error

if not exist .env (
  copy .env.example .env >nul
  echo.
  echo Created a new .env from .env.example.
  echo Fill in your Twitch credentials before running the live bot.
) else (
  echo.
  echo Existing .env found. Keeping it unchanged.
)

echo.
echo Setup complete.
echo Test locally with: run_simulator.bat
echo Start Twitch with:   run_bot.bat
echo Web Hub sync:        run_portal_sync.bat
echo.
pause
exit /b 0

:install_error
echo.
echo ERROR: Dependency installation failed.
echo Verify internet access and Python 3.11+ then run setup_windows.bat again.
pause
exit /b 1
