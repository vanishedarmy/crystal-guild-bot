# Crystal Guild v1.8.1 — Validation Report

## Automated validation

- Bot Python suite: **738/738 PASS**.
- Hosted Web/API Python suite: **78/78 PASS**.
- Frontend Node regression suite: **670/670 PASS**.
- Python compileall: **PASS** for Bot and hosted Web modules.
- JSON integrity audit: **PASS**.
- Expansion Merc artwork: **18/18 required WebP cards present** (6 Heroes × Locked / Available / Unavailable), all below 400 KB.

## Focused coverage

- Schema 18 creates persistent `player_merc_recruits` records.
- Founding Mercs remain available without permanent recruitment rows.
- Quest recruitment blocks until its listed progression requirements are met.
- Gil recruitment deducts the permanent contract cost exactly once and remains replay-safe.
- Expansion Heroes cannot be deployed before permanent recruitment.
- Locked silhouette, Available, and Unavailable artwork routing is verified.
- `MERC_RECRUIT` is accepted through Portal Action protocol 35.
- Dungeon action, choice, continue, and retreat payloads preserve positive room `revision` values through the hosted gateway.

## Build environment

The source archive intentionally does not ship `node_modules`, so the Vite production bundle command is not used as a release gate in this workspace. The source/regression suites, direct artwork checks, Python compilation, and data integrity checks are the release validation gates.
