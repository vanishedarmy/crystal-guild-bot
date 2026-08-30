@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set BOT_AUTH=http://localhost:4343/oauth?scopes=user:read:chat%%20user:write:chat%%20user:bot^&force_verify=true
set OWNER_AUTH=http://localhost:4343/oauth?scopes=channel:bot%%20channel:read:subscriptions^&force_verify=true

:menu
cls
echo ============================================================
echo       CRYSTAL GUILD v1.4.0 - DUNGEONS & DELVES TWITCH AUTH HELPER
echo ============================================================
echo.
echo IMPORTANT: run_cloud_token_authorization.bat MUST already be running for cloud-token setup.
echo.
echo 1. Authorize the DEDICATED BOT account
echo    Login to Twitch as the bot account before approving.
echo.
echo 2. Authorize the BROADCASTER / OWNER account
echo    Login to Twitch as the channel owner before approving.
echo.
echo 3. Show both authorization URLs without opening them
echo    Useful when using an Incognito/Private browser window.
echo.
echo 0. Exit
echo.
set /p AUTH_CHOICE=Choose an option: 

if "%AUTH_CHOICE%"=="1" goto bot
if "%AUTH_CHOICE%"=="2" goto owner
if "%AUTH_CHOICE%"=="3" goto show
if "%AUTH_CHOICE%"=="0" exit /b 0
pause
goto menu

:bot
echo.
echo Opening BOT authorization URL.
echo Confirm the Twitch account shown by Twitch is your DEDICATED BOT account.
start "" "%BOT_AUTH%"
pause
goto menu

:owner
echo.
echo Opening OWNER authorization URL.
echo Confirm the Twitch account shown by Twitch is your STREAMER/BROADCASTER account.
echo This authorization also grants channel:read:subscriptions for tier perks.
start "" "%OWNER_AUTH%"
pause
goto menu

:show
echo.
echo BOT ACCOUNT URL:
echo http://localhost:4343/oauth?scopes=user:read:chat%%20user:write:chat%%20user:bot^&force_verify=true
echo.
echo BROADCASTER / OWNER URL:
echo http://localhost:4343/oauth?scopes=channel:bot%%20channel:read:subscriptions^&force_verify=true
echo.
echo Tip: use a Private/Incognito window for the bot account so you do not
echo accidentally authorize the wrong Twitch account.
echo.
pause
goto menu
