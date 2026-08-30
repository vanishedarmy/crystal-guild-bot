# Crystal Guild v1.5.0 — Trails & Raids Alpha 4 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **556 / 556 PASS**.
- Frontend Node regression suite: **420 / 420 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

## Alpha 4 coverage
- Titan — Heart of the Crag scripted Trial data and mechanic cycle are regression-covered.
- **Landslide** Defend response, missed-response knockdown, **Granite Gaol** restraint/rescue, **Heart of the Crag** interception/damage check, weakened/empowered **Earthen Fury**, and zero-retaliation compatibility are covered.
- A restrained raider cannot queue or resolve actions; destroying the Gaol releases the exact restrained target.
- Existing boss-directed damage automatically routes to active Titan mechanic adds, preserving the established chat action surface with no new target command.
- Hosted Overlay sanitization removes internal Gaol target/release IDs while retaining public mechanic/add state.
- The Trial & Raid Board remains collapsible with remembered state and canonical right-hand-closed / down-hand-open pointer behavior.
- Alpha 1 Ifrit, Alpha 2 Shiva, Alpha 3 Ramuh, and unscripted raids remain green in the full regression suites.

## Source / asset validation
- Python compile sweep: **102 / 102 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **204 / 204 PASS**.
- Plain JS/MJS `node --check`: **163 / 163 PASS**.
- GameData: **37 bosses / 4 Dungeons / 0 errors**.
- Public artwork: **0 PNG / 575 WebP**.
- Literal frontend image-route audit: **152 / 152 PASS**, 0 missing.

## Upgrade / recovery drill
- Real Alpha 3 schema-10 database reopened under Alpha 4: **PASS**.
- Existing test-player level/Gil preserved exactly (**Lv.17 / 4,321 Gil**): **PASS**.
- No schema migration was triggered: **PASS**.
- SQLite quick-check and foreign-key check: **PASS**.
- Runtime checkpoint and non-destructive backup/restore verification: **PASS**.

## Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-a4`.
- Local DB schema **10**, hosted sync **1**, Portal Action protocol **25**, Twitch prefix `!`.
- No migration, reset, OAuth/environment change, new environment variable, Dungeon change, or reward/economy rebalance.

## Packaging verification
- Alpha 3 → Alpha 4 Bot delta: **32 changed/new, 0 deleted**; final **156 files**.
- Alpha 3 → Alpha 4 Web delta: **57 changed/new, 0 deleted**; final **831 files**.
- Full archives and individual/paired patch helpers reconstruct the exact frozen Alpha 4 trees: **156/156 Bot** and **831/831 Web PASS**.
- Release ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **PASS**.
