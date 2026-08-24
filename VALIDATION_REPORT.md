# Crystal Guild v1.1.16 — Arsenal Hotfix 1 Validation Report

## Certification summary

**PASS — timed autonomous Hunts and the website readability pass are certified on the v1.1.16 Arsenal schema-5 / protocol-14 baseline.**

| Check | Result |
|---|---:|
| Bot automated tests | **366 / 366 PASS** |
| Frontend source/unit/regression tests | **168 / 168 PASS** |
| Hosted Portal/API tests | **40 / 40 PASS** |
| Python grammar sweep | **74 / 74 PASS** |
| JS/JSX/MJS independent TypeScript parse | **103 / 103 PASS** |
| 1,000-player / 10,000-op / 4-reader stress | **PASS** |

## Timed Hunt contracts

Automated and targeted coverage verifies:

- exact rank timers: **C 5m / B 15m / A 30m / S 1h / S+ 2h**;
- accepting a new Hunt does not occupy the shared `active_encounter` slot;
- rewards are deferred until the timed assignment resolves;
- early resolution is rejected;
- daemon resolution does not occur before the deadline and does occur when due;
- active Hunt deadlines are present in persisted/runtime combat state;
- only one Hunt may be active per player while different players may Hunt concurrently;
- build/recovery activity is locked while that hero is away;
- Hunt cooldown covers the assignment duration;
- automatic consumable ceilings are enforced by rank;
- survival logic does not indiscriminately spend rare recovery items;
- timed Hunt state survives runtime checkpoint/restore;
- Hunt combat metrics and normal reward/record paths remain intact;
- Twitch command dispatch only wakes the scheduler; chat activity is not the resolution trigger;
- Solo Venture and shared combat state remain independent;
- legacy pre-hotfix Hunt checkpoints remain compatible.

## Website contracts

The Adventure Board and site regressions verify:

- active timed Hunt state, countdown, progress, and assignment duration are presented to players;
- new Hunt copy explicitly states that chat combat is not required;
- old new-Hunt Twitch-round instructions are absent;
- Portal, Streamer Dashboard, and Player Guide include the Hotfix 1 readability safeguards;
- long text can wrap without forcing card/grid overflow;
- mobile action targets and Hunt-progress layouts remain usable at narrow widths;
- current Arsenal functionality, Portal protocol behavior, and hosted routes continue to pass the complete existing suites.

## Stress result

Synthetic cloud profile:

- Players: **1,000**
- Operations: **10,000**
- Concurrent Portal readers: **4**
- Portal reads: **6,898**
- Elapsed: **15.04 s**
- Throughput: **664.9 ops/s**
- Ledger rows: **12,594**
- SQLite quick-check failures: **0**
- Foreign-key violations: **0**
- Negative Gil states: **0**
- Negative inventory states: **0**
- Portal read errors: **0**
- Transaction rollbacks: **0**

## Compatibility

- Runtime: `1.1.16-arsenal-h1`
- Frontend asset revision: `1.1.16-arsenal1h1`
- Local DB schema: **5**
- Hosted sync schema: **1**
- Hosted sync compatibility: `1.1.15-wayfarer`
- Portal Action protocol: **14**
- Twitch prefix: `!`

No database migration, player reset, new Render secret, or new Twitch OAuth scope is introduced.

Build-environment note: a full local Vite production bundle is not part of this certification because the frontend dependency tree is not installed in this execution environment. Frontend regressions, independent syntax parsing, hosted API tests, and release-package verification cover the shipped source; Render performs the normal production dependency install/build during deployment.
