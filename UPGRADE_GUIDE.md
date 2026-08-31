# Crystal Guild v1.5.1 — Relic Arsenal Complete Upgrade Guide

## Supported baseline
Upgrade in place from **v1.5.0 — Trails & Raids**. The Web patch is based on the current **v1.5.0 Web Hotfix 4** tree and carries those scenic-layer fixes forward.

## Upgrade
1. Stop the local/cloud Bot worker before replacing source files.
2. Back up the live `crystal_guild.db` and preserve `.env`, Twitch token storage, hosted secrets, and persistent-disk data.
3. Apply the Bot patch or replace with the full v1.5.1 Bot tree.
4. Apply the Web Hotfix 4 → v1.5.1 Web patch or replace with the full v1.5.1 Web tree.
5. Deploy/restart the matching Bot and Web builds.
6. Verify `!cgversion`, `!health`, and `/api/health` report `1.5.1-relic-arsenal-complete`.
7. Open the Relics page and confirm the collection denominator is 18; confirm an active Hunt keeps its scenic art on the result card after resolution.

No migration or player reset is required. Schema remains 10, hosted sync 1, Portal protocol 25, and prefix `!`.

If the Web source is older than v1.5.0 Hotfix 4, use the full v1.5.1 Web package rather than the incremental Web patch.
