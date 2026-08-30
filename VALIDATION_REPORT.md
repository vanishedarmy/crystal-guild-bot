# Crystal Guild v1.5.0 — Trails & Raids Alpha 3 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **550 / 550 PASS**.
- Frontend Node regression suite: **415 / 415 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

## Alpha 3 coverage
- Ramuh — Judgment Spire scripted Trial data and mechanic cycle are regression-covered.
- **Rolling Thunder** chaining, **Levinshare** Defend-based stack sharing, **Judgment Charge** Grounding progress, weakened/empowered **Judgment Bolt**, and zero-retaliation compatibility are covered.
- The Trial & Raid Board is collapsible, remembers its disclosure state, and uses the canonical right-hand-closed / down-hand-open pointer behavior.
- Live Raid presentation covers chain, shared-hit, and Grounding Gauge mechanics while preserving Alpha 2 add HP, Break/Stagger, and role-aware contribution presentation.
- Alpha 1 Ifrit and Alpha 2 Shiva behavior remain green in the full regression suites.
- Existing unscripted raids retain their established action surface and reward behavior.

## Source / asset validation
- Python compile sweep: **101 / 101 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **203 / 203 PASS**.
- Plain JS/MJS `node --check`: **162 / 162 PASS**.
- GameData: **37 bosses / 4 Dungeons / 0 errors**.
- Public artwork: **0 PNG / 575 WebP**.
- Literal frontend image-route audit: **151 / 151 PASS**, 0 missing.

## Upgrade / recovery drill
- Real Alpha 2 schema-10 database reopened under Alpha 3: **PASS**.
- Existing test-player level/Gil preserved exactly (**Lv.17 / 4,321 Gil**): **PASS**.
- No schema migration was triggered: **PASS**.
- SQLite quick-check and foreign-key check: **PASS**.
- Non-destructive backup/restore verification: **PASS**.

## Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-a3`.
- Local DB schema **10**, hosted sync **1**, Portal Action protocol **25**, Twitch prefix `!`.
- No migration, reset, OAuth/environment change, new environment variable, Dungeon change, or reward/economy rebalance.

## Packaging verification
- Alpha 2 → Alpha 3 Bot delta: **31 changed/new, 0 deleted**; final **155 files**.
- Alpha 2 → Alpha 3 Web delta: **56 changed/new, 0 deleted**; final **830 files**.
- Full archives and individual/paired patch helpers reconstruct the exact frozen Alpha 3 trees: **155/155 Bot** and **830/830 Web PASS**.
- Release ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **PASS**.
