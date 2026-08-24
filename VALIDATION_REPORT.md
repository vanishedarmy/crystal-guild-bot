# Crystal Guild v1.1.16 — Arsenal Hotfix 4 Validation Report

## Feature validation

PASS — `!clearadventures` is registered as a streamer-only Twitch command and uses the existing shared owner gate.

PASS — `!clearventures` is retained as a convenience alias while `!clearadventures` remains the documented canonical command.

PASS — the engine recovery operation clears the shared field/Rally encounter and encounter roster.

PASS — all timed Hunt assignments are removed from authoritative runtime state and the empty set is persisted through the combat checkpoint.

PASS — all schema-5 `solo_expeditions` rows are deleted directly, so an orphaned Solo Venture can be recovered even when Portal cannot render it.

PASS — an active raid/world boss remains untouched.

PASS — adventure cooldowns remain untouched; `!resettimers` remains the separate explicit timer reset.

PASS — Streamer Dashboard documents the new recovery command and its scope.

## Source regression suites

- Bot automated tests: **368 / 368 PASS**
- Frontend automated tests: **171 / 171 PASS**
- Hosted Portal/API tests: **45 / 45 PASS**
- Python grammar: **74 / 74 PASS**
- JavaScript / JSX / MJS syntax parse: **104 / 104 PASS**

Expected simulated-error log messages in the Bot tests (notification outage, action acknowledgement loss, corrupt recovery fixture, Twitch status lookup failures) remained test fixtures and did not fail the suite.

## Synthetic concurrency stress

Configuration:

- 1,000 players
- 10,000 mutation operations
- 4 concurrent Portal readers

Result:

- elapsed: **16.38 s**
- throughput: **610.3 ops/s**
- Portal reads: **7,557**
- SQLite journal mode: **WAL**
- quick-check failures: **0**
- foreign-key violations: **0**
- negative Gil rows: **0**
- negative inventory rows: **0**
- Portal read errors: **0**
- transaction rollbacks: **0**

**CLOUD RUNTIME STRESS PASS**

## Release identity

- Bot runtime: `1.1.16-arsenal-h4`
- Web runtime: `1.1.16-arsenal-h4`
- frontend asset revision: `1.1.16-arsenal1h4`
- local DB schema: **5**
- hosted sync schema: **1**
- Portal Action protocol: **14**

Package extraction/overlay verification is recorded after release archives are assembled.

## Exact release-package verification

PASS — extracted Complete archive matches the finalized Hotfix 4 source tree exactly: **0 diff lines**.

PASS — extracted standalone Bot archive matches the finalized Bot tree exactly: **0 diff lines**.

PASS — extracted standalone Web archive matches the finalized Web tree exactly: **0 diff lines**.

PASS — applying `CrystalGuild-v1.1.16-Arsenal-Hotfix4-Update-from-Hotfix3.zip` over an untouched Arsenal Hotfix 3 Complete tree reproduces the finalized Hotfix 4 tree exactly: **0 diff lines**.

Suites rerun from the extracted Complete archive:

- Bot: **368 / 368 PASS**
- Frontend: **171 / 171 PASS**
- Hosted Portal/API: **45 / 45 PASS**
