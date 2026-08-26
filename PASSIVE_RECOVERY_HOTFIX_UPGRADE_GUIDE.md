# Passive Recovery Hotfix — Bot Upgrade

1. Back up the current database.
2. Replace Bot files with this package.
3. Keep the existing database, `.env`, Twitch token database, and Portal sync key.
4. Start the Bot and verify `!cgversion` reports `1.1.18-recovery-h1`.
5. No database migration is required. The new inactivity and stream-session markers use the existing `runtime_state` table.
