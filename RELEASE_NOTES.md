# Crystal Guild v1.4.0 — Dungeons & Delves Beta 3

## Final Beta shared-state hardening

Beta 3 keeps the four-Dungeon feature freeze and focuses on simultaneous-action safety, replay/restart continuity, and release-candidate readiness. No fifth Dungeon, new currency, reward tuning, or non-Dungeon balance pass is included.

### Cross-connection serialization
- Authoritative state-guarded mutations now acquire SQLite write intent before their first live-state read.
- Two separate Bot/engine connections sharing the same Guild database cannot both validate and spend the same Dungeon revision.
- The existing in-process lock still orders local calls; the database transaction now extends that guarantee across independent connections/processes using the same database.
- Run ID + chamber ID + persisted revision remain the exact Dungeon state contract.

### Replay and restart safety
- Repeated delivery of the **same Portal action ID** still returns the committed receipt and does not advance combat, route choice, retreat, or settlement twice.
- Replay resolution remains compatible with stale-state rejection: a legitimate retry of an already committed action is safe even after state has advanced.
- Dungeon revision and run state continue to survive restart/reconnect.
- Two-connection concurrency regressions cover different action IDs, duplicate action-ID delivery, and competing continue/retreat decisions.

### Feature freeze
- Dungeon catalog remains Forgotten Ossuary, Emberglass Foundry, Whiteglass Bastion, and Riftglass Observatory.
- Existing Crossroads effects, weighted Events, encounter pressure, first-clear rewards, Cache settlement, records, and Bestiary integration are unchanged.
- Adventure state remains **15,368 bytes**, leaving **1,016 bytes** below the 16 KiB guardrail with all four Dungeons unlocked.

### Compatibility
- Bot runtime: `1.4.0-dungeons-b3`
- Hosted Web/frontend: `1.4.0-dungeons-b3`
- Local DB schema: **10** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **25** unchanged from Beta 1
- Twitch prefix: `!`
- Database migration: **none**
- Player reset: **none**
- OAuth/environment changes: **none**
- New environment variables: **none**
- Gameplay/economy rebalance: **none**

Beta 3 should deploy as a paired Web + Bot update so the hosted UI and authoritative concurrency hardening advance together.
