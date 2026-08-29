# Validation Report — Crystal Guild v1.3.0 Guild Expansion Alpha 1

## Result
**PASS**

## Automated validation
- Bot Python suite: **448 / 448 PASS**.
- Frontend Node suite: **329 / 329 PASS**.
- Hosted Web/API Python suite: **47 / 47 PASS**.
- Focused Guild Expansion Alpha 1 tests: **5 / 5 PASS** (included in Bot total).
- Python source compilation: **82 / 82 PASS**.
- JS/JSX/MJS source parsing: **175 / 175 PASS**.
- Explicit routed artwork references: **221 checked, 0 missing**.

## Alpha 1 coverage
- Public Fellowship snapshot exposes exactly five major facilities: Guild Hall, Workshop, Chocobo Stables, Guild Archive, Airship Dock.
- Major facilities present a compact **Lv. 0–3** path.
- Airship Dock is seeded at Lv. 0 and remains visibly locked for future construction.
- Available public construction projects exclude old support facilities and future Airship construction.
- Guild Hall/Workshop/Stable/Archive projects combine Gil/material/gameplay/Fellowship requirements as applicable.
- A schema-8 v1.2-style database seeds the new Airship Dock row without a database migration or player reset.
- Existing high legacy facility tiers are not downgraded; their stored values and existing shared effects remain intact.
- Existing legacy projects remain readable/completable through the compatibility path so an upgrade cannot strand an active project.
- Player Guide describes the facility/construction loop in player-facing language and avoids backend implementation jargon.
- What's New leads with Guild Expansion Alpha 1.

## Compatibility
- Bot runtime: `1.3.0-guild-expansion-a1`
- Hosted Web runtime: `1.3.0-guild-expansion-a1`
- Frontend asset revision: `1.3.0-guild-expansion-a1`
- Local DB schema: **8** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **20** unchanged
- Twitch prefix: `!`
- Player reset: **none**
- Database migration: **none**
- OAuth changes: **none**
- New environment variables: **none**

## Build note
The source package intentionally does not vendor `node_modules`; normal hosted deployment installs the pinned frontend dependencies before building. Source parsing and the complete frontend regression suite pass against the shipping tree.

## Package verification
- v1.2.0 → Alpha 1 Web patch: **35 changed/new files, 0 deletions**, exact reconstruction of **796 / 796** shipping Web files.
- v1.2.0 → Alpha 1 Bot patch: **16 changed/new files, 0 deletions**, exact reconstruction of **137 / 137** shipping Bot files.
- ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 manifest: **PASS**.
