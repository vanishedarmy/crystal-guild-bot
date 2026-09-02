# Crystal Guild v1.7.0 — Moogle Emporium Annex Alpha 3 — Render Cloud Setup

Preserve the worker's persistent `/var/data` state and all Render environment secrets. Never delete or overwrite the live authoritative database while applying this hotfix.

Persistent paths remain:
```text
/var/data/crystal_guild.db
/var/data/twitch_tokens.db
/var/data/overlay/state.json
/var/data/backups/
```

Routine file logs now use `/tmp/crystal-guild-logs`; Render's service log stream remains the normal place to review runtime logs.

Cloud Storage Hotfix 3 automatically prunes old `crystal_guild-startup-*.db` files **before** creating the next startup backup. It retains at most two startup copies and leaves migration backups such as `pre_schema_15_*.db` untouched. If the persistent disk still cannot safely fit a new copy, startup continues without a new backup and emits a warning instead of crashing.

Deploy this Bot build and restart the worker. Verify `!cgversion` reports `1.7.0-emporium-annex-a3h3`, schema **15**, Portal protocol **31**, and `!health` is clean. The existing Item Usage Copy Hotfix 2 Web build (`1.7.0-emporium-annex-a3h2`) remains compatible and does not need to be changed.

If the worker starts but later reports SQLite write failures, the disk is being consumed by something other than startup backups. In that case archive/delete unnecessary non-authoritative files from `/var/data` or increase the Render disk size. Do not delete `crystal_guild.db`.

Before reconnecting a moved/restored worker, run `python run_cloud_preflight.py`. The hosted raid overlay route remains `/overlay`.
