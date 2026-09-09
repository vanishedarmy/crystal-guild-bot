# Crystal Guild v1.7.1 — Render Cloud Setup

Preserve the worker's persistent `/var/data` state and all Render environment secrets. Never delete or overwrite the live authoritative database during deployment.

Persistent paths:
```text
/var/data/crystal_guild.db
/var/data/twitch_tokens.db
/var/data/overlay/state.json
/var/data/backups/
```

Routine file logs use `/tmp/crystal-guild-logs`; Render's service log stream remains the normal place to review runtime logs.

The Bot prunes old `crystal_guild-startup-*.db` files **before** creating the next startup backup, retains at most two startup copies, and leaves migration backups such as `pre_schema_15_*.db` and `pre_schema_16_*.db` untouched. If the persistent disk cannot safely fit another backup, startup continues with a warning instead of crashing.

Deploy the v1.7.1 Resynthesis Alpha 2 Hotfix 5 Gear Favorites Authority Fix Bot and the matching v1.7.1 Resynthesis Alpha 2 Web build together, then restart the worker. Startup creates and verifies `pre_schema_16_*.db` before the additive schema migration. Verify `!cgversion` reports `1.7.1-resynthesis-a2h5`, schema **16**, Portal protocol **33**, and `!health` is clean.

If the worker later reports SQLite write failures, inspect other non-authoritative files consuming `/var/data` or increase the Render disk size. Do not delete `crystal_guild.db`.

Before reconnecting a moved/restored worker, run `python run_cloud_preflight.py`. The hosted raid overlay route remains `/overlay`.
