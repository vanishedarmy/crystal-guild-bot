# Crystal Guild v1.4.0 — Dungeons & Delves Alpha 4

## Dungeon Encounter & Event Expansion

Alpha 4 builds on Alpha 3 with a fourth high-level delve, weighted Dungeon Event chambers, richer room outcomes, and encounter-specific miniboss/boss pressure. Existing Dungeon persistence, run/chamber stale-tab binding, replay protection, retreat/defeat settlement, Crossroads route effects, and first-clear records remain intact.

### The Riftglass Observatory
- Adds the fourth persistent Dungeon: **The Riftglass Observatory**.
- Unlock: character **Lv. 34** plus **55% The Astral Scar** Expedition exploration.
- Recommended level: **38**.
- Ten chambers with two Crossroads, one weighted Event chamber, a Death Machine miniboss, sanctuary, and Crystal Wolf finale.
- Dungeon identity: **Anomalies & Pressure**.

### Dungeon Events
- Adds the new **Event** room type without adding a new Portal action or database table.
- Event rooms select from validated weighted outcomes and can restore or drain resources, damage/heal the hero, add Dungeon Cache XP/JP/Gil/items, record discoveries, or shape a later hazard/combat.
- Event outcomes are resolved authoritatively and persisted with the active Dungeon run.

### Encounter rules and opening pressure
- Dungeon combat rooms can define their own round limit, opening HP/resource pressure, temporary enemy statuses, and player-facing mechanic notes.
- The Riftglass Observatory miniboss begins protected and must be defeated within 10 rounds.
- The final Crystal Wolf begins with Haste/brief Regen, drains 12% max MP/AP on entry, and has a 9-round collapse window.
- Existing player-paced Dungeon combat, items, abilities, Defend, Bestiary credit, and cache settlement remain unchanged.

### Richer room outcomes
- Treasure, hazard, sanctuary, Crossroads, and Event rooms now share a validated effect engine.
- Forward modifiers remain restart-safe and are consumed only by the relevant later room.
- Existing first-clear bonuses and Dungeon reward identities remain intact.

### Payload hardening
- Empty optional Dungeon/Hunt fields are omitted where the Web already has safe defaults.
- With all four Dungeons unlocked, the Adventure-state payload serializes to **15,475 bytes**, leaving **909 bytes** below the 16 KiB transport guardrail.

### Compatibility
- Bot runtime: `1.4.0-dungeons-a4`
- Hosted Web runtime: `1.4.0-dungeons-a4`
- Frontend asset revision: `1.4.0-dungeons-a4`
- Local DB schema: **10** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **24** unchanged
- Twitch prefix: `!`
- Database migration: **none from Alpha 3**
- Player reset: **none**
- OAuth/environment changes: **none**
- Non-Dungeon gameplay/economy rebalance: **none**
