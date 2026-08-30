# Crystal Guild v1.5.0 — Trails & Raids Alpha 5 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **562 / 562 PASS**.
- Frontend Node regression suite: **425 / 425 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

## Alpha 5 coverage
- Garuda — Eye of the Storm scripted Trial data and full mechanic cycle are regression-covered.
- **Slipstream** Defend response and missed-response Slow pressure are covered.
- **Friction** containment and uncontained party splash are covered.
- **Plume Squadron** creates sanitized Satin/Razor Plume adds that intercept existing boss-directed damage without a new target command.
- **Aerial Blast** resolves weakened, pressurized, or empowered according to surviving Plumes.
- The Trial & Raid Board remains collapsible with remembered state and canonical right-hand-closed / down-hand-open pointer behavior.
- Flagship Trial cards use the Alpha 5 spacious two-column desktop layout with wider copy, separated metadata/stats/commands, and one-column tablet/mobile fallbacks.
- Alpha 1 Ifrit, Alpha 2 Shiva, Alpha 3 Ramuh, Alpha 4 Titan, and unscripted raids remain green in the full regression suites.

## Source / asset validation
- Python compile sweep: **103 / 103 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **205 / 205 PASS**.
- Plain JS/MJS `node --check`: **164 / 164 PASS**.
- GameData: **37 bosses / 4 Dungeons / 0 errors**.
- Public artwork: **0 PNG / 575 WebP**.
- Active literal frontend image-route audit: **153 / 153 PASS**, 0 missing.
- All **5 / 5** flagship Trial artwork routes resolve in the shipping tree.

## Upgrade / recovery drill
- Real Alpha 4 schema-10 database reopened under Alpha 5: **PASS**.
- Existing test-player level/Gil preserved exactly (**Lv.17 / 4,321 Gil**): **PASS**.
- No schema migration was triggered: **PASS**.
- SQLite quick-check and foreign-key check: **PASS**.
- Runtime checkpoint and non-destructive backup/restore verification: **PASS**.

## Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-a5`.
- Local DB schema **10**, hosted sync **1**, Portal Action protocol **25**, Twitch prefix `!`.
- No migration, reset, OAuth/environment change, new environment variable, Dungeon change, or reward/economy rebalance.

## Packaging verification
- Alpha 4 → Alpha 5 Bot delta: **39 changed/new, 0 deleted**; final **157 files**.
- Alpha 4 → Alpha 5 Web delta: **58 changed/new, 0 deleted**; final **832 files**.
- Full archives and individual/paired patch helpers reconstruct the exact frozen Alpha 5 trees: **157/157 Bot** and **832/832 Web PASS**.
- Release ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **10 / 10 PASS**.
