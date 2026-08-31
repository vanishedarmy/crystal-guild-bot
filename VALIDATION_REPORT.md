# Crystal Guild v1.5.1 — Relic Arsenal Complete Validation Report

## Regression suites
- Bot: **601 / 601 PASS** plus **30 subtests PASS**.
- Frontend: **469 / 469 PASS**.
- Hosted Web/API: **47 / 47 PASS**.

## Source validation
- Python compile sweep: **110 / 110 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **214 / 214 PASS**.
- Plain JS/MJS Node syntax sweep: **173 / 173 PASS**.
- `portal.css` independent parser: **0 errors**.

## GameData and artwork
- **18 Jobs / 18 Relics / 435 items / 37 bosses / 4 Dungeons / 0 GameData errors**.
- New Relic artwork: **30 / 30** present, 512×512, transparent, independently decodable.
- Public artwork: **0 PNG / 611 WebP**.
- WebP decode: **611 / 611 PASS**.
- Static literal WebP routes: **168 / 168 resolve**; dynamic region artwork: **8 / 8 resolve**.

## Upgrade / recovery
A genuine v1.5.0 schema-10 database was copied and reopened under v1.5.1:
- schema remained **10**;
- **no pre-migration backup was triggered** because no migration was required;
- validation hero remained **Lv.17 / 4,321 Gil**;
- SQLite quick-check and foreign-key validation were clean;
- backup/restore reopened at schema 10 with the same hero state.

## Production frontend build gate
`npm run build` was explicitly attempted in this container. It could not execute because the local source environment does not contain the pinned Vite executable (`sh: vite: not found`, exit 127). The release therefore does **not** claim a local Vite-build pass. The exact CSS defect class encountered during v1.5.0 was independently parsed cleanly, and the complete frontend regression/parser suites pass.

## Release delta
- Bot: **38 changed/new, 0 deleted → 164 files**.
- Web: **92 changed/new, 0 deleted → 877 files**.

## Package verification
- Verified final trees: **164 Bot files / 877 Web files**.
- The v1.5.0 → v1.5.1 Bot patch, Web Hotfix 4 → v1.5.1 Web patch, paired updater, full packages, and complete archive reconstruct those trees exactly.
- Final release gate: **6/6 ZIP CRC PASS**, **0 hygiene violations**, and **10/10 SHA-256 entries verified**.

