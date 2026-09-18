# Crystal Guild v1.8.1 — Render Cloud Setup

Keep the Bot's persistent database on the mounted disk (normally `/var/data/crystal_guild.db`) and Twitch token storage on persistent disk as configured by the existing deployment. Do not replace the live database with a packaged blank database.

Before upgrading, keep your normal external backup. On first startup against a schema-17 database, v1.8.1 also creates and verifies an automatic `pre_schema_18_<timestamp>.db` backup before applying the additive Merc Recruitment migration.

Deploy the **v1.8.1 Merc Recruitment Bot and matching Web build together**, then restart the worker. Verify `!cgversion` reports `1.8.1-merc-recruitment`, schema **18**, Portal Action protocol **35**, and `!health` is clean.

The hosted Web process and Bot must use the same Portal sync credentials and protocol version. The Web action gateway now requires the Dungeon room `revision` field for action, choice, continue, and retreat requests.

Use `run_cloud_preflight.py` before production rollout where applicable. OBS overlay routes remain available under `/overlay`.

## Persistent state compatibility

The deployment layout remains compatible with the persistent-disk setup used by the v1.7.1 release line. The default Twitch token database path is `/var/data/twitch_tokens.db`; preserve that file alongside `/var/data/crystal_guild.db` during upgrades.
