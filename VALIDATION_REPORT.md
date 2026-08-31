# Crystal Guild v1.5.0 — Trails & Raids Beta 1 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **580 / 580 PASS**.
- Frontend Node regression suite: **440 / 440 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

## Beta 1 coverage
- Trial Chronicle persistence is regression-covered across all seven scripted flagship Trials.
- Existing Alpha-era boss-clear history is merged into the Chronicle without conversion or reset.
- Beta 1 records tracked wipes, fastest successful clear round, best contribution score, best damage, best healing, and best mitigation through the existing generic record-stat system.
- Unique Trial clears drive the visible mastery ladder: **Unproven → Trial Initiate → Trial Vanguard → Primal Conqueror → Coilbreaker**.
- Unscripted raids do not create Trial Chronicle metrics.
- The Adventure Board and Records page render the same authenticated Chronicle data while Raid combat remains Twitch/Bot-authoritative.
- Ifrit, Shiva, Ramuh, Titan, Garuda, Leviathan, Bahamut, ordinary raids, and all four production Dungeons remain green.

## Source / asset validation
- Python compile sweep: **106 / 106 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **208 / 208 PASS**.
- Plain JS/MJS `node --check`: **167 / 167 PASS**.
- GameData: **37 bosses / 4 Dungeons / 0 errors**.
- Public artwork: **0 PNG / 575 WebP**.
- Static literal image routes: **155 / 155 unique paths resolve**, 0 missing; Beta 1 adds/removes **0** image routes versus Alpha 7.
- All **7 / 7** flagship Trial artwork routes resolve in the shipping tree.

## Upgrade / recovery drill
- Real Alpha 7 schema-10 database reopened under Beta 1: **PASS**.
- Existing test-player level/Gil preserved exactly (**Lv.17 / 4,321 Gil**): **PASS**.
- No schema migration was triggered: **PASS**.
- SQLite quick-check and foreign-key check: **PASS**.
- Non-destructive backup/restore verification: **PASS**.

## Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-b1`.
- Local DB schema **10**, hosted sync **1**, Portal Action protocol **25**, Twitch prefix `!`.
- No migration, reset, OAuth/environment change, new environment variable, Trial reward rebalance, Dungeon change, or new Portal mutation.

## Packaging verification
- Alpha 7 → Beta 1 Bot delta: **31 changed/new, 0 deleted**; final **160 files**.
- Alpha 7 → Beta 1 Web delta: **59 changed/new, 0 deleted**; final **835 files**.
- Full archives and individual/paired patch helpers reconstruct the exact frozen Beta 1 trees: **160/160 Bot** and **835/835 Web PASS**.
- Release ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **10 / 10 PASS**.
