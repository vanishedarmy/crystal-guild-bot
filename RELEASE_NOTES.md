# Crystal Guild v1.4.0 — Dungeons & Delves Alpha 2

## Routes, Risk & a Second Delve

Alpha 2 expands the persistent Dungeon foundation without changing established Guild, Expedition, Hunt, combat, or economy balance outside Dungeons.

### Two persistent Dungeons
- **The Forgotten Ossuary** now contains **8 chambers** and adds a Crossroads route decision while preserving its Lv. 10 + 25% Emerald Wilds unlock.
- **The Emberglass Foundry** joins the Dungeon Board as a second **8-chamber** delve, unlocking at **Lv. 18 + 35% Ashen Highlands exploration**.
- The Foundry introduces its own combat, treasure, hazard, miniboss, sanctuary, final boss, completion bonus, and visual identity.

### Crossroads route choices
- New **choice chambers** pause progression until the player deliberately selects a route.
- Safer routes can preserve or restore HP/MP/AP.
- Riskier routes can deal immediate damage in exchange for additional Gil, materials, or other Dungeon Cache value.
- Named route discoveries are carried with the active delve and shown in the final Dungeon report.
- Portal route choices are replay-safe and remain bound to the exact run/chamber shown in the submitting browser tab.

### Dungeon Board expansion
- Dungeon cards now show scene art, minimum/recommended level, chamber count, route-choice count, unlock state, and permanent progress.
- Active runs show their Dungeon scene, current discoveries, route options when a Crossroads is reached, persistent condition, Cache, combat controls, and history.
- The Player Guide now documents both current Dungeons and Crossroads behavior.

### Shared UI cleanup
- The retro collapse hand keeps the established state language: **right when closed, down when open**.
- All supported collapsible surfaces now share one canonical rendered pointer size so Overview/What’s New controls do not appear oversized relative to Adventure Board, Fellowship, Streamer Dashboard, or Player Guide disclosures.

### Payload / stability discipline
- The Adventure-state payload remains below the existing 16 KiB regression ceiling even with a second Dungeon by omitting redundant Hunt fields that the frontend does not consume.
- Alpha 1 persistent Dungeon state, restart recovery, cache settlement, stale-tab protection, and `!clearadventures` behavior remain intact.

## Compatibility
- Bot runtime: `1.4.0-dungeons-a2`
- Hosted Web runtime: `1.4.0-dungeons-a2`
- Frontend asset revision: `1.4.0-dungeons-a2`
- Local DB schema: **10** unchanged from Alpha 1
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **24** (advances from 23 for `DUNGEON_CHOICE`)
- Twitch prefix: `!`
- Database migration from Alpha 1: **none**
- Player reset: **none**
- OAuth changes: **none**
- New environment variables: **none**
- Existing non-Dungeon gameplay/economy changes: **none**

Because the Portal Action protocol advances, deploy the matching Alpha 2 Web and Bot together.
