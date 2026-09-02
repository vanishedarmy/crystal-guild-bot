# Crystal Guild v1.7.0 — v1.7.0 Production Final — Simplified Render Setup

1. Preserve `/var/data/crystal_guild.db`, Twitch tokens, overlay state, and all environment secrets.
2. Deploy this **Bot** build and restart the worker.
3. Keep the existing Item Usage Copy Hotfix 2 Web build; no Web redeploy is required.
4. Confirm `!cgversion` = `1.7.0`, schema = **15**, Portal protocol = **31**, and `!health` is clean.
5. Confirm the Render log no longer shows `database or disk is full` during `create_startup_backup`.

The Bot automatically prunes excess startup backups before creating a new one. No player reset or database migration is required.
