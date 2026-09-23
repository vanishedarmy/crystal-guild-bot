# Crystal Guild — Records & Moments Alpha 10 Validation

**Scope:** cumulative Steps 1–7 based on v1.9.0 Alpha 9 Player Language Hotfix 1; new release identity `1.9.0-records-moments-alpha10`.

## Source-level regression

| Gate | Result |
| --- | --- |
| Full Bot unittest suite | **894/894 passed** |
| Hosted Web/API unittest suite | **85/85 passed** |
| Full frontend Node suite | **748/805 passed, 57 failed** |
| Frontend Step 6 failure-name comparison | **57/57 inherited, zero newly failing names** |
| Focused Records/Moments Steps 4–7 frontend checks | **22/22 passed** |
| Newly introduced Step 7 frontend checks | **7/7 passed** |
| Release identity | Alpha 10 matches Bot, hosted API, Guide metadata, Web and package metadata |
| Local database schema | **23**, no new Step 7 migration |
| Hosted sync / Portal Action protocol | **1 / 37**, unchanged |
| Individual Moment/Trophy assets | **16/16 individual WebPs**, matching Step 5 SHA-256; matching independent PNGs available in standalone pack |

## Explicit limitations

The 57 outstanding frontend assertions are identical by test name to the Step 6 baseline. Many refer to older release identities or historical frontend/layout contracts; none are counted as passing. Newly modified current-release assertions were updated to Alpha 10 while preserving earlier feature and asset verification. A fully passing frontend regression suite is **not** established.

The current runtime lacks installed React/Vite dependencies and cannot access the npm registry (`EAI_AGAIN`). Consequently a dependency-installed Vite production bundle and actual deployed desktop/mobile React browser walkthrough could **not** be completed here. A static responsive CSS/source audit and targeted frontend regression checks passed; this does not substitute for real browser verification on staging. Do not treat these source-level gates as proof of production readiness.

## Release identity and migration

Local schema **23**; existing schema 22 is migrated with an automatic verified `pre_schema_23_*` backup. Existing Bestiary, career/Trial records, Titles, seasonal records, Guild economy and Hall of Trophies ownership are preserved. Historical Moments are awarded **only** for verified saved single purchases and five consecutive paid Mini Cactpot losses. No older combat/Hunt/Raid/World Event Moment is guessed from aggregated totals.

## Recommended deployment gate

Install pinned Web dependencies in an environment with registry access and run `npm run build`; run full Node/hosted suites on the exact deployed source; validate owned/unowned secret Moments, Trophy Hall, Records cards, Player Guide and responsive mobile layout against a staging environment. Preserve all actual SQLite databases, Twitch tokens, `.env`, `overlay/state.json` and hosted secrets. Only replace production with matching Alpha 10 Bot/Web after the staging walkthrough and the inherited test-failure assessment are acceptable to you.
