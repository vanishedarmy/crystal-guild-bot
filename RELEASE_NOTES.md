# Crystal Guild v1.1.19 — Retro Phase III / Chocobo Portraits

This paired Bot + Web update adds persistent Chocobo portrait selection to the existing Chocobo Stable.

## Chocobo portrait persistence
- `player_chocobos` now stores a persistent `portrait_id`.
- Existing registered Chocobos migrate automatically to `classic_gold` without changing names, Bond XP, traits, registration dates, or any other progression.
- The authoritative portrait catalog contains 10 IDs shared with the Web Stable: Classic Gold, Midnight, Celestial, Ember, Verdant, Cobalt, Arcane, Sandrunner, Frost, and Rose.
- Invalid portrait IDs are rejected.
- Portrait changes are replay-safe through the existing Portal action receipt system.
- Public player snapshots now include the selected Chocobo portrait so read-only profiles render the owner’s choice.

## Portal action
New typed action: `SET_CHOCOBO_PORTRAIT` with `{ "portrait_id": "..." }`.

Portal Action protocol advances **14 → 15**. The matching iii13 Web build must be deployed with this Bot.

## Database migration
Local DB schema advances **5 → 6** by adding `player_chocobos.portrait_id TEXT NOT NULL DEFAULT 'classic_gold'`.

Before the migration, Crystal Guild automatically creates and verifies a `pre_schema_6_<timestamp>.db` backup for an existing on-disk Guild.

## Compatibility
- Bot runtime: `1.1.19-retro-phase-iii-chocobo1`
- Local DB schema: **6**
- Hosted sync schema: **1** unchanged
- Hosted sync compatibility: `1.1.15-wayfarer` unchanged
- Portal Action protocol: **15**
- Twitch command prefix: `!` unchanged
- Player reset: **none**
- OAuth changes: **none**
- New environment variables: **none**
