# Crystal Guild Bot v1.1.14 — Cloud Continuity

This release keeps the v1.1.13 always-on Render architecture and adds self-healing hosted-state continuity plus the transport side of the hosted OBS raid overlay. Gameplay balance and persistent player schema are unchanged.

## Identity

- Runtime `1.1.14-cloud-continuity`
- DB schema 4
- Hosted sync schema 1
- Portal Action protocol 12
- Twitch prefix `!`

## Cloud Continuity changes

The normal Portal heartbeat now republishes the Fellowship snapshot and sanitized raid overlay state. A Web redeploy can rebuild those ephemeral hosted views without a Bot restart. Overlay sync uses the existing `PORTAL_SYNC_KEY`; it does not expose Twitch credentials or the authoritative SQLite database.

The Render Blueprint keeps the 1 GB `/var/data` disk and intentionally omits the unsupported `maxShutdownDelaySeconds` field. The Python 3.11 Records formatting correction is also included.

Existing v1.1.13 cloud installs update source in-place; do not re-upload `crystal_guild.db` or `twitch_tokens.db`. See `UPGRADE_GUIDE.md`.
