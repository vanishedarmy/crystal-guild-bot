# Finalization Audit — Crystal Guild v1.7.0 Retainer Service Alpha 2

**Decision: PASS — canonical Alpha 2 baseline.**

Alpha 2 is built from the verified v1.7.0 Retainer Service Alpha 1 baseline. This pass contains **no new artwork**; Retainer artwork and visual polish are intentionally deferred to the next step.

## Release contract

- Runtime/frontend: `1.7.0-retainer-a2`
- Database schema: **15**
- Hosted sync: **1**
- Portal Action protocol: **31**
- Prefix: `!`
- Baseline: verified v1.7.0 Retainer Service Alpha 1

## Scope freeze

Alpha 2 adds the focused Retainer expansion only:

1. optional route-specific Priority material selection;
2. one guaranteed normal material roll for the selected target;
3. explicit focused Gil prices while preserving Alpha 1 general prices;
4. persistent eight-entry Retainer collection history;
5. additive schema-15 history storage;
6. protocol-31 optional `priority` payload support;
7. Portal, Player Guide, What’s New, and release-contract updates.

Assignment durations, general prices, base roll counts, Retainer EXP, Rank thresholds, bonus odds, single-assignment concurrency, dispatch-time reward commitment, and exactly-once collection are unchanged. Relic/Artifact materials remain unavailable.

## Upgrade safety

Schema 14→15 is additive. A live-assignment migration drill preserved player progression, Gil, inventory, MGP, Retainer profile state, and the already-committed Alpha 1 assignment payload exactly. The generated `pre_schema_15_*.db` backup passed SQLite `PRAGMA quick_check` and remained schema 14.

## Regression and source gates

- Bot: **655/655 PASS**
- Frontend: **534/534 PASS**
- Hosted Web/API: **60/60 PASS**
- Bot Python parse: **115/115 PASS**
- Web Python parse: **14/14 PASS**
- Combined Python parse: **129/129 PASS**
- JS/MJS syntax: **195/195 PASS**
- CSS structural checks: **8/8 PASS**
- WebP decode: **815/815 PASS**
- Public PNG count: **0**

The source-only Web package does not contain installed `node_modules`, so no local Vite production-build pass is claimed.

## Economy / exploit review

Priority procurement redirects one existing normal roll and costs a 25–30% Gil premium. It never adds reward rolls, time efficiency, EXP, Rank progress, or bonus-find probability. Only materials already present in the route are selectable. The highest modeled all-haul resale conversion is Mineral Survey at roughly **+206 Gil/hour**, bounded by a two-hour timer and the single active-Retainer limit; no additional sell restriction is required for Alpha 2.

## Packaging verification

- **PASS** — Alpha 1→Alpha 2 Bot patch reproduces the verified Alpha 2 Bot tree byte-for-byte, excluding runtime-only overlay state that is intentionally not package-managed.
- **PASS** — Alpha 1→Alpha 2 Web patch reproduces the verified Alpha 2 Web tree byte-for-byte.
- **PASS** — full Bot and Web ZIPs reproduce their verified source trees byte-for-byte after extraction.
- **PASS** — Complete ZIP contains byte-identical verified Bot and Web trees.
- **PASS** — all five release ZIPs pass archive-integrity checks.
- **PASS** — all five ZIPs are free of live databases, exact `.env` files, Python caches/bytecode, `node_modules`, and runtime overlay/checkpoint state.
- Bot overlay patch contains **66** changed/new source files; Web overlay patch contains **77** changed/new source files.
- SHA-256 checksums are supplied in the release checksum manifest.

## Deferred intentionally

- Retainer artwork and visual polish
- Moogle Emporium Annex / Guild building expansion

No artwork file was generated or changed in Alpha 2.
