# Validation Report — Crystal Guild v1.7.0 — Retainer Service Alpha 2

**Result: PASS**

## Release contract

- Runtime/frontend: `1.7.0-retainer-a2`
- Local DB schema: **15**
- Hosted sync schema: **1**
- Portal Action protocol: **31**
- Twitch command prefix: `!`
- Baseline: verified v1.7.0 Retainer Service Alpha 1
- Artwork changes: **none**

## Automated regression

- Bot: **655 / 655 PASS**
- Frontend: **534 / 534 PASS**
- Hosted Web/API: **60 / 60 PASS**
- Bot Python parse: **115 / 115 PASS**
- Web Python parse: **14 / 14 PASS**
- JS/MJS syntax: **195 / 195 PASS**
- CSS structural checks: **8 / 8 PASS**
- WebP decode: **815 / 815 PASS**
- Public PNG count: **0**

The source package does not include installed `node_modules`, so no local Vite production build is claimed.

## Alpha 2 feature checks

Targeted procurement was verified to:

- accept an optional Priority material only from the selected assignment route;
- charge the route's focused Gil cost;
- guarantee one normal 1–2 quantity roll of that material;
- preserve the original total base roll count;
- leave remaining rolls weighted/mixed;
- leave bonus-find chance independent;
- commit the complete reward payload at dispatch;
- survive restart without rerolling;
- preserve exactly-once collection semantics.

Recent Retainer history was verified to:

- persist collected route, target, rewards, bonus, fee and EXP;
- write exactly one history record per assignment even after an idempotent replay;
- return the eight most recent collected assignments to the Portal.

## Schema 14 → 15 migration drill

**PASS.** A real Alpha 1 schema-14 database was created with a recruited Lv.17 player, 17 Iron Ore, 777 MGP, an existing Retainer profile and a live Mineral Survey assignment. The assignment had already paid its 500-Gil fee, leaving 3,821 Gil.

Opening that database with Alpha 2:

- advanced schema **14 → 15**;
- created `retainer_history` additively;
- preserved Lv.17 and **3,821 Gil** exactly;
- preserved **17 Iron Ore** and **777 MGP** exactly;
- preserved Retainer XP/statistics exactly;
- preserved the active Alpha 1 assignment ID, type, cost, committed `reward_json`, dispatch time, return time and state exactly;
- created a `pre_schema_15_*.db` backup;
- the backup passed SQLite `PRAGMA quick_check` and remained at schema 14.

No player reset or Retainer reassignment is required.

## Balance

See `RETAINER_SERVICE_ALPHA2_BALANCE_AUDIT.md`. Focused dispatches pay a **25–30%** Gil premium and redirect exactly one existing base roll rather than adding a roll. Timers, general prices, Retainer EXP, Rank thresholds, one-assignment limit and bonus-find odds remain unchanged from Alpha 1. Relic and Artifact materials remain excluded.
## Packaging verification

The final Alpha 2 packaging drill passed: both Alpha 1→Alpha 2 overlay patches reproduce the verified Alpha 2 source trees (excluding runtime-only overlay state), the full Bot/Web archives reproduce their sources, the Complete archive contains matching Bot/Web trees, all five ZIPs pass integrity tests, and the safety scan found no live databases, exact `.env` files, Python caches/bytecode, `node_modules`, or runtime overlay/checkpoint state.

