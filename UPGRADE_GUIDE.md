# Crystal Guild v1.1.16 — Arsenal Hotfix 4 Upgrade Guide

Upgrade baseline: **v1.1.16 — Arsenal Hotfix 3**.

## Normal upgrade

1. Stop/restart the Bot worker as you normally would for a Bot code update.
2. Preserve runtime/private files such as `.env`, `.tio.tokens.json`, `crystal_guild.db`, the Twitch token database, and Render persistent-disk data.
3. Overlay the Hotfix 4 update onto the existing Arsenal Hotfix 3 installation, or replace Bot/Web from the full packages.
4. Push the matching Web files to GitHub and redeploy Render.
5. Start/restart the Bot worker.
6. Verify `!cgversion` reports `1.1.16-arsenal-h4`.
7. Verify Web `/api/health` reports frontend asset revision `1.1.16-arsenal1h4`.

There is **no schema migration** in this hotfix. Local DB schema remains 5 and Portal Action protocol remains 14.

## Clearing the currently stuck adventure

After Hotfix 4 is live, run in Twitch chat from the configured streamer/owner account:

`!clearadventures`

This immediately clears:

- any active shared field/Rally encounter;
- all timed Hunt assignments;
- all persisted Solo Ventures, including orphaned/stuck rows.

It does **not** clear raids/world bosses or player progression.

The command also leaves all adventure cooldowns intact. If you deliberately want those timers reset too, run `!resettimers` separately afterward.

## Expected result

The Bot replies with a count of the adventure state it cleared. In the hosted/cloud runtime, Portal sync is woken immediately; refresh the Adventure Board if an already-open browser tab still shows stale content.
