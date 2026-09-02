# Upgrade to v1.7.0 Alpha 3 — Cloud Storage Hotfix 3

This is a **Bot-only operational hotfix** from Item Usage Copy Hotfix 2.

- Bot runtime: `1.7.0-emporium-annex-a3h3`
- Compatible Web frontend: `1.7.0-emporium-annex-a3h2` (unchanged)
- Local DB schema: **15** (unchanged)
- Hosted sync: **1** (unchanged)
- Portal Action protocol: **31** (unchanged)
- Prefix: `!`

Preserve `/var/data/crystal_guild.db`, `/var/data/twitch_tokens.db`, overlay state, and all live secrets. No database migration or player reset is required.

Deploy the Hotfix 3 Bot and restart the worker. During startup it automatically removes excess `crystal_guild-startup-*.db` copies before attempting the new backup. If those old startup copies caused the full disk, the worker should recover on this deployment without manually deleting the authoritative database.

Do **not** delete `crystal_guild.db`. Migration backups named `pre_schema_*.db` are also left untouched by automatic retention.
