# Validation Report — Crystal Guild v1.2.0 Expeditions Beta 1

## Result
**PASS — Beta 1 balance, simulation, compatibility, and regression validation complete.**

## Automated suites
- Bot: **437 / 437 PASS**
- Hosted Web/API: **47 / 47 PASS**
- Frontend Node regression suite: **307 / 307 PASS**
- Python compilation: **PASS**

Expected simulated network-loss, Twitch-auth, corrupt-checkpoint, and recovery warnings emitted by resilience tests were observed; those tests passed.

## Balance validation
- Fixed-seed Expedition matrix: **3,000 runs** across 75 scenarios.
- Safe/Unknown/Push Deeper pressure is mechanically distinct, not only descriptive.
- Legendary final-boss HP/pressure smoothing is covered by dedicated tests.
- Existing Alpha 2–5 Expedition progression, regional bosses, Atlas, Legendary contracts, regional discovery, Chocobo specialties, accomplishments, and Hunt Seal stipends remain covered.
- Adventure Board compact-state regression remains below the established **16 KB** guardrail; new pressure multipliers are kept Bot-authoritative rather than enlarging the Portal payload.
- Alpha 5 stipend values remain unchanged after the economy audit.

## Package validation
- Alpha 5 → Beta 1 Bot patch: **16 changed/new files, 0 deleted; exact reproduction PASS**.
- Alpha 5 → Beta 1 Web patch: **29 changed/new files, 0 deleted; exact reproduction PASS**.
- Full Bot, full Web, direct patches, paired update, and Complete ZIP integrity: **PASS**.
- Runtime/secret hygiene scan: **PASS**; no live `.env`, token store, SQLite database/WAL/SHM, bytecode/cache directories, `node_modules`, or log files are packaged.
- SHA-256 manifest generated after final archive creation.

## Release identity
- Bot runtime: `1.2.0-expeditions-b1`
- Hosted Web runtime: `1.2.0-expeditions-beta1`
- Frontend revision: `1.2.0-expeditions-b1`
- Local DB schema: **8**
- Hosted sync schema: **1**
- Portal Action protocol: **20**
- Player reset/migration: **none**

## Production bundle note
The source package intentionally does not include `node_modules`, so a local Vite production bundle is not part of this validation environment. The full source-level frontend suite, hosted/API suite, JSX/source parsing exercised by the regressions, and Python compilation are clean.
