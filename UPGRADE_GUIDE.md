# Upgrade Guide — Crystal Guild v1.6.0 Gold Saucer Alpha 1

Supported baseline: **v1.5.1 — Relic Arsenal Complete**. For Web patch installs, first have the **v1.5.1 Relic Artwork Refresh Hotfix 1** applied; otherwise use the full Alpha 1 Web package.

1. Stop the active Bot worker before replacing source files.
2. Back up `crystal_guild.db` and preserve `.env`, Twitch token storage, hosted secrets, and persistent-disk data.
3. Apply the v1.5.1 → Alpha 1 Bot patch or replace with the full Alpha 1 Bot tree.
4. Apply the v1.5.1 Relic Artwork Refresh → Alpha 1 Web patch or replace with the full Alpha 1 Web tree.
5. Deploy/restart the matching Bot and Web together because Portal Action protocol advances to **26**.
6. On first Bot startup, schema **10 → 11** runs automatically after creating and verifying a pre-migration backup.
7. Verify `!cgversion`, `!health`, and `/api/health` report runtime `1.6.0-gold-saucer-a1`, hosted sync **1**, and Portal protocol **26**.
8. Open your character → **Gold Saucer**. Confirm the 500 SP welcome purse appears once, Mini Cactpot opens, Crystal Slots resolves, and the Prize Counter lists cosmetic Titles.
9. On a later UTC day, the first Saucer visit grants the 50 SP floor allowance exactly once.

Do **not** delete or replace the live database. Existing character, Guild, Chocobo, Expedition, Dungeon, Trial/Raid, Relic, title, inventory, and economy progression is preserved in place.
