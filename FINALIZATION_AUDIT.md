# v1.7.0 Retainer Service Alpha 1 — Finalization Audit

## Release decision

**PASS — canonical Alpha 1 baseline.** Built from the final v1.6.0 Gold Saucer production source with additive Retainer persistence, Portal actions, and matched Portal UI support.

## Contract

- Runtime `1.7.0-retainer-a1`
- Local DB schema **14**
- Hosted sync **1**
- Portal Action protocol **30**
- Prefix `!`
- v1.6.0 Gold Saucer/MGP gameplay and balance unchanged
- Existing player database/progression preserved by sequential migration with a verified pre-schema-14 backup

## Retainer invariants

- One personal Retainer per recruited player.
- One active or returned-awaiting-collection assignment at a time.
- Dispatch uses Gil and is exactly-once through Portal action idempotency.
- Material rewards are rolled and persisted at dispatch; refresh/reconnect/restart cannot reroll the haul.
- Pending rewards remain hidden until return.
- Collection grants canonical crafting materials and Retainer EXP exactly once.
- Bonus finds are stored separately from the main haul and granted once.
- Alpha 1 material pools exclude Relic and Artifact rarity.
- Retainers do not hold player gear and do not participate in combat.

## Upgrade safety

A real final-v1.6.0 schema-13 database was migrated to schema 14. The drill preserved a level-17 player, 4,321 Gil, 17 Iron Ore, and 777 MGP exactly. The generated `pre_schema_14_*.db` backup passed SQLite `quick_check` and retained schema 13/player state.

## Automated gates

- Bot regression: **649 / 649 PASS**
- Retainer focused regression: **8 / 8 PASS**
- Bot Python AST parse: **114 / 114 PASS**
- Schema migration drill: **PASS**
- Retainer procurement balance audit: **PASS for Alpha 1**

The existing test suite emits expected simulated outage/recovery messages and pre-existing ResourceWarnings in several legacy tests; these do not represent failed gates.

## Packaging gates

- **PASS** — the v1.6.0→Alpha 1 Bot patch reproduces the full Alpha 1 Bot source byte-for-byte after application to a clean v1.6.0 Bot baseline.
- **PASS** — the full Bot ZIP reproduces the verified Alpha 1 Bot source byte-for-byte after extraction.
- **PASS** — the Complete package contains a byte-identical copy of this verified Bot tree.
- **PASS** — all release ZIPs pass archive-integrity checks and exclude live databases, `.env`, Python caches/bytecode, and runtime overlay/checkpoint state.
