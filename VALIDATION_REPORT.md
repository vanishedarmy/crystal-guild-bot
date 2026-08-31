# Crystal Guild v1.5.0 — Trails & Raids Alpha 6 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **568 / 568 PASS**.
- Frontend Node regression suite: **430 / 430 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

## Alpha 6 coverage
- Leviathan — Tidebreak Expanse scripted Trial data and full mechanic cycle are regression-covered.
- Tidal Sweep side targeting and individual Defend response are covered.
- Undertow HP/resource pressure and unbraced party splash are covered.
- Maelstrom Surge coordinated Defends and Stability Gauge success are covered.
- Tidal Wave weak/empowered resolution and sanitized public mechanic state are covered.
- Alpha 5's two-column desktop Trial layout, responsive fallback, persistent collapse state, and canonical pointer remain intact.
- Ifrit, Shiva, Ramuh, Titan, Garuda, unscripted raids, and all four production Dungeons remain green.

## Source / asset validation
- Python compile sweep: **104 / 104 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **206 / 206 PASS**.
- Plain JS/MJS `node --check`: **165 / 165 PASS**.
- GameData: **37 bosses / 4 Dungeons / 0 errors**.
- Public artwork: **0 PNG / 575 WebP**.
- Active literal frontend image-route audit: **154 / 154 PASS**, 0 missing.
- All **6 / 6** flagship Trial artwork routes resolve in the shipping tree.

## Upgrade / recovery drill
- Real Alpha 5 schema-10 database reopened under Alpha 6: **PASS**.
- Existing test-player level/Gil preserved exactly (**Lv.17 / 4,321 Gil**): **PASS**.
- No schema migration was triggered: **PASS**.
- SQLite quick-check and foreign-key check: **PASS**.
- Non-destructive backup/restore verification: **PASS**.

## Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-a6`.
- Local DB schema **10**, hosted sync **1**, Portal Action protocol **25**, Twitch prefix `!`.
- No migration, reset, OAuth/environment change, new environment variable, Dungeon change, or reward/economy rebalance.

## Packaging verification
- Alpha 5 → Alpha 6 Bot delta: **31 changed/new, 0 deleted**; final **158 files**.
- Alpha 5 → Alpha 6 Web delta: **57 changed/new, 0 deleted**; final **833 files**.
- Full archives and individual/paired patch helpers reconstruct the exact frozen Alpha 6 trees: **158/158 Bot** and **833/833 Web PASS**.
- Release ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **10 / 10 PASS**.
