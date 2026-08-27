# Crystal Guild v1.1.19 — Retro Phase III / Chocobo Portraits Validation Report

## Automated validation

- Bot unittest suite: **392 / 392 PASS**.
- Python test run completed against the finalized Chocobo Portrait Bot source.
- Chocobo migration, persistence, portrait mutation, snapshot publication, invalid-ID rejection, and Portal replay/idempotency behavior are covered by the packaged regression suite.

## Chocobo portrait feature checks

- Existing schema-5 installations migrate additively to schema **6**.
- Existing registered Chocobos receive `classic_gold` as the default portrait without changing name, Bond XP, traits, registration data, inventory, or other player progression.
- The authoritative portrait catalog exposes exactly 10 supported IDs.
- `SET_CHOCOBO_PORTRAIT` accepts supported portrait IDs and rejects unknown IDs.
- Selected portrait IDs persist in `player_chocobos` and are published through player snapshots.
- Portal action replay safety remains active for portrait changes.
- Facility Supply Balance monster-drop changes from the previous paired checkpoint remain present.

## Compatibility

- Bot runtime: `1.1.19-retro-phase-iii-chocobo1`
- Local DB schema: **6**
- Hosted sync schema: **1** unchanged
- Hosted sync compatibility identity: `1.1.15-wayfarer` unchanged
- Portal Action protocol: **15**
- Twitch prefix: `!` unchanged
- Player reset: **none**
- OAuth changes: **none**
- New environment variables: **none**
