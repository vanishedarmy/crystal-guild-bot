# Crystal Guild v1.5.0 — Trails & Raids Alpha 7 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **574 / 574 PASS**.
- Frontend Node regression suite: **435 / 435 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

## Alpha 7 coverage
- Bahamut — The Final Coil scripted Trial data and recurring mechanic cycle are regression-covered.
- Akh Morn shared-hit coordination and Megaflare Tower Defend success are covered.
- Critical-HP Teraflare Charge unlock and public Overlay sanitization are covered.
- Bahamut's full-width capstone Board treatment, Player Guide coverage, OBS mechanic rendering, and current What's New are frontend-covered.
- Ifrit, Shiva, Ramuh, Titan, Garuda, Leviathan, unscripted raids, and all four production Dungeons remain green.

## Source / asset validation
- Python compile sweep: **105 / 105 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **207 / 207 PASS**.
- Plain JS/MJS `node --check`: **166 / 166 PASS**.
- GameData: **37 bosses / 4 Dungeons / 0 errors**.
- Public artwork: **0 PNG / 575 WebP**.
- Literal frontend image-route audit: **165 / 165 PASS**, 0 missing.
- All **7 / 7** flagship Trial artwork routes resolve in the shipping tree.

## Upgrade / recovery drill
- Real Alpha 6 schema-10 database reopened under Alpha 7: **PASS**.
- Existing test-player level/Gil preserved exactly (**Lv.17 / 4,321 Gil**): **PASS**.
- No schema migration was triggered: **PASS**.
- SQLite quick-check and foreign-key check: **PASS**.
- Non-destructive backup/restore verification: **PASS**.

## Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-a7`.
- Local DB schema **10**, hosted sync **1**, Portal Action protocol **25**, Twitch prefix `!`.
- No migration, reset, OAuth/environment change, new environment variable, Dungeon change, or reward/economy rebalance.

## Packaging verification
- Alpha 6 → Alpha 7 Bot delta: **31 changed/new, 0 deleted**; final **159 files**.
- Alpha 6 → Alpha 7 Web delta: **58 changed/new, 0 deleted**; final **834 files**.
- Full archives and individual/paired patch helpers reconstruct the exact frozen Alpha 7 trees: **159/159 Bot** and **834/834 Web PASS**.
- Release ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **10 / 10 PASS**.
