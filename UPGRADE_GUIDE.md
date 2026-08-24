# Crystal Guild v1.1.16 — Arsenal Upgrade Guide

## Upgrade from v1.1.15 Wayfarer Hotfix 3

Arsenal is an in-place-safe **Bot + Web** content/gameplay update. Local DB schema remains **5**, hosted sync schema remains **1**, and Portal Action protocol remains **14**. No database migration runs.

1. Stop the Crystal Guild Bot/worker cleanly.
2. Keep the normal backup of `crystal_guild.db` and preserve all private/runtime state.
3. Apply the **v1.1.15 Wayfarer Hotfix 3 → v1.1.16 Arsenal Update** package over the existing installation, or replace with the full Bot/Web packages as appropriate.
4. Preserve `.env`, `.tio.tokens.json`, `crystal_guild.db`, `/var/data/twitch_tokens.db` (cloud installations), and other private runtime files.
5. Push/deploy the matching Arsenal Web files to GitHub/Render.
6. Restart the Bot/worker.
7. Verify `!cgversion` / `!health` reports runtime **`1.1.16-arsenal`**.
8. Verify Web `/api/health` reports frontend asset revision **`1.1.16-arsenal1`**.
9. Open Jobs and confirm active abilities appear across JLv.1/8/15/22/30/40 with element/effect information.
10. Check the Adventure Board for the new Lv.2/4/6/8 Hunts and the Player Guide/Streamer references for the new early World Bosses and recipes.

## No migration step

Do **not** manually edit SQLite or rerun the Wayfarer schema migration. Existing schema-5 databases remain schema 5. Player progression, Solo Venture state, Titles, inventory, equipment, crafting progression, Fellowship, Chocobo progression, cooldowns, and records remain authoritative in the existing database.

## Release identity

- Product: **Crystal Guild v1.1.16 — Arsenal**
- Runtime: `1.1.16-arsenal`
- Frontend: `1.1.16-arsenal1`
- Local DB schema: **5**
- Hosted sync schema: **1**
- Hosted sync compatibility: `1.1.15-wayfarer`
- Portal Action protocol: **14**
- Twitch prefix: `!`

No new Render secret or Twitch authorization is required.
