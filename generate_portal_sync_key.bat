@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" generate_portal_sync_key.py
) else (
  python generate_portal_sync_key.py
)
echo.
echo Copy this value into PORTAL_SYNC_KEY on BOTH the hosting service and your local .env.
pause
