@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Crystal Guild v1.1.16 - Arsenal - Bot Control Panel

:menu
cls
echo ============================================================
echo              CRYSTAL GUILD v1.1.16 - ARSENAL
echo                    BOT CONTROL PANEL
echo ============================================================
echo.
echo  1. First-Time Setup / Install Dependencies
echo  2. Edit Configuration (.env)
echo  3. Resolve Twitch User IDs into .env
echo  4. Run Bot Self-Test
echo  5. Start Local Simulator (No Twitch Required)
echo  6. Start Twitch Bot
echo  7. Open Twitch Authorization Helper
echo  8. Start Hosted Web Hub Sync
echo  9. Test Web Hub Sync Once
echo 10. Generate Web Hub Sync Key
echo 11. Start OBS Raid Overlay
echo 12. Open Logs Folder
echo 13. Open Full Setup README
echo 14. Open Web Sync Setup Notes
echo 15. Run Release Readiness Check
echo 16. Create Verified Database Backup
echo 17. Run Non-Destructive Recovery Drill
echo 18. Run Synthetic Stress Test
echo 19. Prepare Private Render Migration Bundle
echo 20. Open Render Cloud Setup Guide
echo 21. Start Cloud Token Authorization Session
echo.
echo  0. Exit
echo.
set /p CG_CHOICE=Choose an option: 

if "%CG_CHOICE%"=="1" goto setup
if "%CG_CHOICE%"=="2" goto env
if "%CG_CHOICE%"=="3" goto ids
if "%CG_CHOICE%"=="4" goto selftest
if "%CG_CHOICE%"=="5" goto simulator
if "%CG_CHOICE%"=="6" goto bot
if "%CG_CHOICE%"=="7" goto auth
if "%CG_CHOICE%"=="8" goto portalsync
if "%CG_CHOICE%"=="9" goto portalsynctest
if "%CG_CHOICE%"=="10" goto synckey
if "%CG_CHOICE%"=="11" goto overlay
if "%CG_CHOICE%"=="12" goto logs
if "%CG_CHOICE%"=="13" goto readme
if "%CG_CHOICE%"=="14" goto websync
if "%CG_CHOICE%"=="15" goto maintenance
if "%CG_CHOICE%"=="16" goto backup
if "%CG_CHOICE%"=="17" goto recovery
if "%CG_CHOICE%"=="18" goto stress
if "%CG_CHOICE%"=="19" goto rendermigration
if "%CG_CHOICE%"=="20" goto renderguide
if "%CG_CHOICE%"=="21" goto cloudauth
if "%CG_CHOICE%"=="0" exit /b 0

echo.
echo Invalid selection.
pause
goto menu

:setup
call setup_windows.bat
goto menu

:env
if not exist .env (
  copy .env.example .env >nul
  echo Created .env from .env.example.
)
start "" notepad.exe ".env"
goto menu

:ids
call resolve_twitch_ids.bat
goto menu

:selftest
call run_selftest.bat
goto menu

:simulator
call run_simulator.bat
goto menu

:bot
start "Crystal Guild Bot" cmd /k call "%~dp0run_bot.bat"
echo Crystal Guild bot launched in a separate window.
pause
goto menu

:auth
call open_twitch_authorization.bat
goto menu

:portalsync
start "Crystal Guild Web Sync" cmd /k call "%~dp0run_portal_sync.bat"
echo Hosted Web Hub sync launched in a separate window.
pause
goto menu

:portalsynctest
call test_portal_sync.bat
goto menu

:synckey
call generate_portal_sync_key.bat
goto menu

:overlay
start "Crystal Guild OBS Overlay" cmd /k call "%~dp0run_overlay.bat"
echo OBS overlay launched in a separate window.
pause
goto menu

:logs
if not exist logs mkdir logs
start "" "%~dp0logs"
goto menu

:readme
start "" notepad.exe "%~dp0FULL_SETUP_README.md"
goto menu

:websync
start "" notepad.exe "%~dp0WEB_SYNC_SETUP.md"
goto menu

:maintenance
call run_maintenance.bat
goto menu

:backup
call backup_database.bat
goto menu

:recovery
call run_recovery_drill.bat
goto menu

:stress
call run_stress_test.bat
goto menu

:rendermigration
if not exist .venv\Scripts\python.exe (
  echo ERROR: Crystal Guild virtual environment is missing. Run setup_windows.bat first.
  pause
  goto menu
)
".venv\Scripts\python.exe" prepare_render_migration.py
pause
goto menu

:renderguide
start "" notepad.exe "%~dp0RENDER_CLOUD_SETUP.md"
goto menu

:cloudauth
call run_cloud_token_authorization.bat
goto menu
