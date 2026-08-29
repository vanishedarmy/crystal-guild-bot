# Crystal Guild v1.4.0 — Dungeons & Delves Alpha 1

## Dungeon Foundations
Alpha 1 introduces Crystal Guild's first persistent, multi-room Dungeon loop while preserving the established v1.3.1 Guild, Expedition, Hunt, economy, and combat balance outside the new Dungeon system.

### The Forgotten Ossuary
- Adds one complete seven-chamber proof-of-concept Dungeon to **Adventure Board → Dungeons & Delves**.
- Unlocks at character **Lv. 10** after reaching **25% Emerald Wilds Expedition exploration**.
- Chamber flow includes an entrance, normal combat, treasure, a hazard, a miniboss, a sanctuary, and a final boss.
- Dungeon runs persist through Portal refreshes, reconnects, and Bot restarts.

### Player-paced Dungeon combat
- Dungeon combat is controlled from the Portal one round at a time with **Attack, Job Ability, Item, and Defend**.
- HP, MP/AP, consumed items, and combat pressure carry from chamber to chamber instead of refreshing after each encounter.
- Dungeon victories feed the existing Bestiary and monster-defeat records.
- The sanctuary chamber provides limited recovery without resetting the run.

### Dungeon Cache & outcomes
- Enemy rewards and chamber treasure accumulate in a temporary **Dungeon Cache** while the run is active.
- Clearing the Dungeon banks **100%** of the cache plus the Dungeon completion bonus.
- Voluntary retreat banks **50%** of the current cache.
- Defeat recovers **25%** of the current cache.
- Clear, defeat, retreat, best-room, and recent-outcome records persist separately from the active run.

### Persistence & safety
- Adds persistent per-player active Dungeon state and permanent Dungeon progress/history.
- Portal Dungeon actions are replay-safe and are bound to the exact **run ID and chamber ID** visible in the submitting browser tab. A stale tab fails closed after another tab advances or replaces the run.
- Only one active adventure can be held at a time; Dungeons block incompatible Venture, Hunt, Expedition, Camp, equipment, shop, crafting, job, and similar mutations while a run is active.
- Streamer emergency `!clearadventures` now clears an active Dungeon run without erasing completed Dungeon records.
- Schema **9 → 10** is additive and creates a verified pre-schema-10 backup before migration.

### Player-facing integration
- Adds Dungeon status, unlock requirements, current chamber, persistent condition, cache, controls, and history to the Adventure Board.
- Adds Dungeons & Delves coverage to the Player Guide.
- Keeps the public **Previous major updates** history limited to shipped stable releases; Alpha 1 appears only as the current What's New entry.

## Compatibility
- Bot runtime: `1.4.0-dungeons-a1`
- Hosted Web runtime: `1.4.0-dungeons-a1`
- Frontend asset revision: `1.4.0-dungeons-a1`
- Local DB schema: **10** (automatic additive migration from schema 9 with verified backup)
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **23** (advances from 22 for Dungeon actions)
- Twitch prefix: `!`
- Player reset: **none**
- OAuth changes: **none**
- New environment variables: **none**
- Existing non-Dungeon gameplay/economy balance changes: **none**
