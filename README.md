# Crystal Guild v1.1.16 — Arsenal Hotfix 4

Arsenal expands every Job to six active Battle Abilities across JLv.1/8/15/22/30/40 and strengthens elemental/special-effect identity throughout the combat catalog. Hotfix 4 adds the streamer-only `!clearadventures` emergency recovery command for orphaned/stuck field adventures, timed Hunts, and persisted Solo Ventures.

Runtime `1.1.16-arsenal-h4` · local DB schema **5** · hosted sync schema **1** · hosted sync compatibility `1.1.15-wayfarer` · Portal Action protocol **14** · Twitch prefix `!`.

`!clearadventures` preserves player progression, inventory, current persisted vitals, cooldowns, camps, shops, achievements, titles, and any active raid/world boss. Use `!resettimers` separately when you intentionally want cooldowns reset too.

No database migration, player reset, new Render secret, or new Twitch OAuth scope is required. Deploy the matching Web build (`1.1.16-arsenal1h4`) so the Streamer Dashboard reference stays aligned.

See `UPGRADE_GUIDE.md`, `RELEASE_NOTES.md`, and `FULL_SETUP_README.md`.
