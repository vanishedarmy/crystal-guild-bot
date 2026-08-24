# Crystal Guild v1.1.16 — Arsenal Validation Report

## Certification summary

**PASS — Arsenal combat/content expansion certified on the v1.1.15 Wayfarer Hotfix 3 schema-5 / protocol-14 baseline.**

Arsenal changes Bot gameplay/content data and matching Web/Guide presentation. It does not change the local database schema, hosted sync schema, hosted sync compatibility contract, or Portal Action protocol.

| Check | Result |
|---|---:|
| Bot automated tests | **362 / 362 PASS** |
| Frontend source/unit/regression tests | **166 / 166 PASS** |
| Hosted Portal/API tests | **40 / 40 PASS** |
| Python AST/grammar sweep | **74 / 74 PASS** |
| JS/JSX independent TypeScript parse | **100 / 100 PASS** |
| GameData validation | **PASS — 0 errors** |
| 1,000-player / 10,000-op / 4-reader stress | **PASS** |
| Update overlay reproduces finalized source | **PASS** |
| Exact extracted Bot/Web/Complete package verification | **PASS** |
| ZIP private/runtime-state hygiene | **PASS** |
| SHA-256 verification | **PASS** |

## Arsenal content contracts

- **18 Jobs × 6 active abilities = 108 active Battle Abilities**.
- Every Job follows active progression at **JLv.1 / 8 / 15 / 22 / 30 / 40**.
- Existing JLv.1/15/30 abilities remain at their prior unlock levels.
- Every Job has multiple elemental or special-effect techniques.
- Ability element/effect traits are exposed by Job details, Player Guide, and Solo Venture ability selection.
- No new multi-target-selection framework is introduced.
- Starter Hunts exist at **Lv.2 / 4 / 6 / 8**, all C-rank with Hunt-only marks.
- Early World Boss progression exists at recommended **Lv.6 / 10 / 14 / 18** before Bomb King.
- Eight new **Lv.3–15** recipes output practical consumables.
- Full `GameData.validate()` returns no errors.

## Stress result

Synthetic cloud profile:

- Players: **1,000**
- Operations: **10,000**
- Concurrent Portal readers: **4**
- Portal reads: **7,512**
- Elapsed: **15.19 s**
- Throughput: **658.3 ops/s**
- Ledger rows: **12,594**
- SQLite quick-check failures: **0**
- Foreign-key violations: **0**
- Negative Gil states: **0**
- Negative inventory states: **0**
- Portal read errors: **0**
- Transaction rollbacks: **0**

## Compatibility

- Runtime: `1.1.16-arsenal`
- Frontend asset revision: `1.1.16-arsenal1`
- Local DB schema: **5**
- Hosted sync schema: **1**
- Hosted sync compatibility: `1.1.15-wayfarer`
- Portal Action protocol: **14**
- Twitch prefix: `!`

No database migration, player reset, new Render secret, or new Twitch OAuth scope is introduced.

Build-environment note: the full local Vite production bundle is not part of this certification because the frontend dependency tree is not installed in this execution environment. Frontend regression tests, independent JS/JSX parsing, hosted API tests, and exact release-package verification all pass; Render performs the normal production dependency install/build during deployment.
