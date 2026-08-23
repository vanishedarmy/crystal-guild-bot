# Crystal Guild v1.1.15 — Wayfarer Validation Report

## Certification summary

**PASS — interactive, persistent Solo Venture gameplay and the player-priority Portal navigation are certified on the v1.1.14 Cloud Continuity Hotfix 3c baseline.**

Wayfarer advances the local database from schema **4 → 5** and the Portal Action protocol from **12 → 13**. Hosted sync schema remains **1**. Existing player progression is preserved through the guarded additive migration.

## Automated validation

- Bot automated tests: **355 / 355 PASS**
- Frontend source/unit/regression tests: **158 / 158 PASS**
- Hosted Portal/API tests: **39 / 39 PASS**
- JavaScript/JSX syntax parse: **97 / 97 PASS**
- Python grammar sweep: **73 / 73 PASS**
- Hotfix 3c → schema 5 migration drill: **PASS**
- Pre-schema-5 backup integrity (`PRAGMA quick_check`): **PASS**
- Migrated database integrity / foreign-key check: **PASS**
- Cloud stress: **1,000 players / 10,000 operations / 4 readers PASS**
- Exact extracted Complete-package Bot tests: **355 / 355 PASS**
- Exact extracted Complete-package hosted Portal/API tests: **39 / 39 PASS**
- Exact extracted Complete-package frontend tests: **158 / 158 PASS**
- Hotfix 3c → Wayfarer single-update overlay: **PASS — final file set and contents match exactly**
- Bot/Web/Complete/Update archive runtime-state hygiene: **PASS**
- Stress elapsed: **15.61 s**
- Stress throughput: **640.6 ops/s**
- Stress Portal reads: **7,249**
- Stress ledger rows: **12,112**
- SQLite quick-check failures: **0**
- Foreign-key violations: **0**
- Negative Gil/inventory states: **0**
- Portal read errors: **0**
- Transaction rollbacks: **0**

Local Vite production bundling was not run because frontend dependencies are not installed in this execution environment. The dependency versions remain pinned; frontend source/regression tests and independent syntax parsing pass.

## Wayfarer regression coverage

Validation confirms that:

- each Solo Venture stage independently uses **60% Encounter / 40% Treasure** odds;
- Solo Venture combat is Portal-only, player-paced, and advances exactly one round after **Attack**, **Ability**, **Use Item**, or **Defend**;
- enemy intent is published before the player's choice;
- learned ability availability, MP/AP costs, Silence restrictions, battle-item ownership, and item consumption are enforced authoritatively;
- Defend advances one round and restores the intended small Job resource amount;
- Solo combat HP/MP/AP/status state persists across rounds and Portal refresh/reconnects;
- an active Solo Venture is stored per player and does not occupy or overwrite the Guild-wide Rally/Hunt encounter state;
- Stage II applies **+15%** and Stage III **+30%** encounter XP/JP/Gil modifiers;
- Treasure remains a 40% event chance at every depth while deeper stages bias chest quality upward;
- Return banks accumulated Venture Spoils; Press On carries current resources and consumed inventory forward;
- secured XP/JP survive defeat or retreat;
- defeat recovers **50%** of unbanked Gil and loses loose item spoils;
- Retreat abandons unbanked Venture Spoils without deleting secured progression;
- build/recovery/resupply/economy actions that would bypass Solo Venture attrition are unavailable while a run is active, while battle items remain usable from the combat interface;
- the existing Rally Venture remains a separate Twitch/live-stream activity;
- Adventurer Portal navigation begins **Overview → Adventure Board → Jobs → Equipment & Inventory** and keeps all established profile destinations;
- the hosted action relay strictly carries protocol-13 Solo Venture action/continue/return/retreat operations and existing replay/idempotency handling remains active.

## Migration drill

A representative schema-4 Hotfix 3c Guild was created with an existing Lv.17 character, XP, Gil, Hunt Seals, HP, inventory, and Solo Venture cooldown state. Opening that same database with Wayfarer:

- created and verified `backups/pre_schema_5_<timestamp>.db` before structural migration;
- preserved the backup at schema 4 with no `solo_expeditions` table;
- migrated the active Guild to schema 5;
- created the per-player `solo_expeditions` table and update index;
- preserved the representative character and inventory values;
- passed `PRAGMA quick_check` and `PRAGMA foreign_key_check` after migration.

## Release identity

- Product: **Crystal Guild v1.1.15 — Wayfarer**
- Bot/Web runtime: `1.1.15-wayfarer`
- Frontend asset revision: `1.1.15-wayfarer1`
- Local DB schema: **5**
- Hosted sync schema: **1**
- Portal Action protocol: **13**
- Twitch prefix: `!`

No player reset, new Render secret, hosted sync schema change, or new Twitch OAuth scope is required. The existing `channel:read:subscriptions` broadcaster authorization remains required only for previously introduced subscriber-tier perks.
