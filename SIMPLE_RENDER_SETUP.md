# Crystal Guild v1.7.1 — Simplified Render Setup

1. Preserve `/var/data/crystal_guild.db`, Twitch tokens, overlay state, and all environment secrets.
2. Deploy the v1.7.1 Resynthesis Alpha 2 Hotfix 1 Bot with the existing Alpha 2 Web build.
3. Confirm `!cgversion` = `1.7.0`, schema = **15**, Portal protocol = **32**, and `!health` is clean.
4. Confirm the Web reports frontend asset revision `1.7.1-resynthesis-a2`.
5. Confirm startup does not report `database or disk is full` while creating a backup.

Startup backup history is pruned before a new copy is attempted. Existing schema-15 v1.7.0 deployments require no player reset or schema migration.
