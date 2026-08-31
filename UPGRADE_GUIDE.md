# Upgrade Guide — v1.6.0 Gold Saucer Alpha 2

Supported baseline: **v1.6.0 Gold Saucer Alpha 1 Hotfix 2** Bot + Web.

1. Stop the Bot worker and hosted Web service.
2. Back up `crystal_guild.db` and preserve `.env`, Twitch token storage, hosted secrets, and persistent-disk data.
3. Apply the H2 → Alpha 2 Bot patch or replace with the full Alpha 2 Bot tree.
4. Apply the H2 → Alpha 2 Web patch or replace with the full Alpha 2 Web tree.
5. Restart/deploy both services together because Portal Action protocol advances to **27**.
6. On first Bot start, schema **11 → 12** runs automatically after creating and verifying a pre-migration backup.
7. Verify `!cgversion`, `!health`, and `/api/health` report `1.6.0-gold-saucer-a2`, hosted sync **1**, Portal protocol **27**, and local schema **12**.
8. Open Gold Saucer and confirm Monster Toss can start, preserve throws through refresh, settle after throw five, and appear in personal records.

Do not replace or delete the live database. Existing characters, Gil, inventory, Fellowship, Chocobos, Expeditions, Dungeons, Trials/Raids, Relics, Titles, Mini Cactpot, Crystal Slots, Saucer Points, Prize Counter purchases, and records are preserved.
