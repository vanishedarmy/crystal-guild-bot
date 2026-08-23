# Crystal Guild v1.1.15 — Wayfarer Hotfix 3 Validation Report

## Certification summary

**PASS — earned Title management through the authenticated Adventurer Portal is certified.**

Hotfix 3 adds the strict `SET_TITLE` Portal mutation while keeping local DB schema **5** and hosted sync schema **1** unchanged. Portal Action protocol advances **13 → 14**.

## Automated results

- Bot automated tests: **356 / 356 PASS**
- Hosted Portal/API tests: **40 / 40 PASS**
- Frontend source/unit/regression tests: **164 / 164 PASS**
- Python grammar/compile sweep: **73 files PASS**
- Synthetic cloud stress: **1,000 players / 10,000 operations / 4 readers PASS**
- Stress throughput: **665.1 ops/s**
- SQLite quick-check failures: **0**
- Foreign-key violations: **0**
- Negative Gil rows: **0**
- Negative inventory rows: **0**
- Portal read errors: **0**
- Transaction rollbacks: **0**

## Release package verification

- Final Complete/Bot/Web archive trees match the finalized source trees exactly: **PASS**
- Direct Hotfix 2 → Hotfix 3 update over an untouched Hotfix 2 Complete package reproduces the finalized Hotfix 3 tree exactly: **PASS**
- Exact extracted Complete package Bot tests: **356 / 356 PASS**
- Exact extracted Complete package hosted Portal/API tests: **40 / 40 PASS**
- Exact extracted Complete package frontend tests: **164 / 164 PASS**
- Runtime/private-state hygiene scan: **PASS** — no player DB, `.env`, `.tio.tokens.json`, or Twitch token DB is packaged.

Build-environment note: a full local Vite production bundle was not run because frontend dependencies are not installed in this execution environment. The pinned dependency contract and frontend source/unit/regression suites pass, and Render performs the normal dependency install/build.

## Title action coverage

Regression coverage verifies that:

- the hosted auth capability list exposes `SET_TITLE` only as a typed Portal action;
- the browser payload accepts only one validated `title_id` field;
- the Bot re-validates the authenticated Twitch identity and the requested Title against authoritative player state;
- an earned Title can be equipped successfully;
- a locked/unearned Title is rejected by the Bot even if manually requested;
- malformed payloads with extra fields are rejected;
- the Portal only shows equip controls on the signed-in player's own profile;
- locked Title cards remain view-only;
- the current Title is visibly marked **Equipped Now**;
- existing Twitch `!title <name>` behavior remains available.

## Compatibility

- Bot/Web runtime: `1.1.15-wayfarer-h3`
- Frontend asset revision: `1.1.15-wayfarer1h3`
- Local DB schema: **5**
- Hosted sync schema: **1**
- Hosted sync compatibility: `1.1.15-wayfarer`
- Portal Action protocol: **14**
- Twitch prefix: `!`

No database migration, player reset, new Render secret, or new Twitch OAuth scope is introduced. Matching Hotfix 3 Bot + Web deployment is required because the Portal Action protocol changes.
