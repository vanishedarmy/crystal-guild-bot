# Validation Report — Crystal Guild v1.2.0 Expeditions RC1

## Result
**PASS — release-candidate validation clean.**

## Automated suites
- Bot Python regression suite: **443 / 443 PASS**.
- Hosted Web/API Python suite: **47 / 47 PASS**.
- Frontend Node regression suite: **326 / 326 PASS**.
- Focused Beta 4 hardening / migration suite: **6 / 6 PASS**.
- Python source compilation: **PASS**.
- JavaScript / JSX TypeScript-parser sweep: **172 files PASS**.

## Player Guide RC cleanup
- Expeditions Player Guide now uses the release-neutral **Expeditions — v1.2** label.
- Beta 1–4 release-history panels are removed from the Guide.
- Alpha 2–5 implementation labels are removed from functional Expedition headings.
- Player-facing Expeditions content retains unlock requirements, regions, routes, saved travel, Cache/return/rescue rules, exploration milestones, Regional Bosses, Mastery, Atlas/Legendary Contracts, landmarks, Journal, Chocobo specialties, Hunt Seal stipends, active-run restrictions, and the quick-use flow.
- Focused guide audit finds **0** matches for release-engineering terms including schema, protocol, SQLite, replay receipt, authoritative, simulation, feature freeze, migration, backend, or frontend in the Expeditions chapter.

## Persistence / migration continuity
The Beta 4 hardening suite remains green in RC1:
- Active Expedition state survives a database/engine restart.
- Long Rest does not heal through an active persistent Expedition.
- Stream-live roster refresh skips active persistent runs while still refreshing idle players once.
- Expedition finish/reward state commits once with its replay receipt.
- A forced replay-receipt failure rolls stage/reward state back rather than partially committing.
- Representative schema-7 progression migrates to schema 8 without reset and produces the verified pre-schema-8 backup.

## Artwork / source audit
- Explicit routed image references checked: **144**.
- Missing explicit routed image references: **0**.
- Beta 2 H2 portrait scenic backgrounds, Expedition artwork, item/gear art, monster art, boss art, Chocobo portraits, Job portraits, and Relic artwork remain packaged.
- Guild Heroes / Player Guide duplicate-airship fix remains covered by frontend regression tests.
- Viewport-positioned detail cards and Beta 3 mobile/accessibility behavior remain covered by frontend regression tests.

## Patch / package verification
- Beta 4 → RC1 Bot patch: **11 changed/new files, 0 deletions**.
- Beta 4 → RC1 Web patch: **31 changed/new files, 0 deletions**.
- Web patch reconstruction against a clean Beta 4 Web tree: **PASS — 795 files exact**.
- Bot patch reconstruction against a clean Beta 4 Bot tree: **PASS — 136 files exact**.
- Full RC1 Web archive versus finalized Web tree: **PASS — 795 files exact**.
- Full RC1 Bot archive versus finalized Bot tree: **PASS — 136 files exact**.
- ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **PASS — 0 violations**.

## Production bundle note
The source release intentionally does not vendor `node_modules`, so a local Vite production bundle is not executed in this clean release tree. Frontend source regression tests and JS/JSX parsing are clean; hosted deployment installs the pinned frontend dependencies before building.

## Compatibility
- Bot runtime: `1.2.0-expeditions-rc1`
- Hosted Web runtime: `1.2.0-expeditions-rc1`
- Frontend asset revision: `1.2.0-expeditions-rc1`
- Local DB schema: **8**
- Hosted sync schema: **1**
- Portal Action protocol: **20**
- Twitch prefix: `!`
- Player reset: **none**
- OAuth change: **none**
- New environment variables: **none**
