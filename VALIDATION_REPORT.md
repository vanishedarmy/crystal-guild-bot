# Crystal Guild v1.5.0 — Trails & Raids Beta 2 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **586 / 586 PASS**.
- Frontend Node regression suite: **445 / 445 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

## Beta 2 coverage
- Repeat-clear mastery derives from the existing boss-clear ledger at 1/3/5/10 clears and requires no backfill or migration.
- Trial Chronicle summary reports Mastered Trials while Beta 1 wipe/fastest/contribution records remain intact.
- The Trial & Raid Board retains a Last Trial Result recap after victory/wipe and shows sanitized action-readiness counts during live combat.
- Every new Raid/Trial has an exact run identity; restored pre-Beta-2 active raids receive a stable compatibility identity.
- Settlement receipts are committed atomically in the existing runtime-state store and bounded to the latest **64** runs.
- A two-engine stale-settlement regression proves the first connection grants the result once while the second applies no duplicate Gil, clear, Fellowship, or Trial record and reloads authoritative runtime state.
- Public Overlay state excludes `raid_instance_id` and internal target IDs.
- Unscripted raids remain outside Trial Chronicle/repeat-mastery classification.
- Ifrit, Shiva, Ramuh, Titan, Garuda, Leviathan, Bahamut, ordinary raids, and all four production Dungeons remain green.

## Source / asset validation
- Python compile sweep: **107 / 107 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **209 / 209 PASS**.
- Plain JS/MJS `node --check`: **168 / 168 PASS**.
- GameData: **37 bosses / 4 Dungeons / 0 errors**.
- Public artwork: **0 PNG / 575 WebP**.
- Static literal image routes: **155 / 155 unique paths resolve**, 0 missing; Beta 2 adds/removes **0** static image routes versus Beta 1.
- All **7 / 7** flagship Trial artwork routes resolve in the shipping tree.

## Upgrade / recovery drill
- Real Beta 1 schema-10 database reopened under Beta 2: **PASS**.
- Existing test-player level/Gil preserved exactly (**Lv.17 / 4,321 Gil**): **PASS**.
- No schema migration was triggered: **PASS**.
- SQLite quick-check and foreign-key check: **PASS**.
- Non-destructive backup/restore verification: **PASS**.

## Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-b2`.
- Local DB schema **10**, hosted sync **1**, Portal Action protocol **25**, Twitch prefix `!`.
- No migration, reset, OAuth/environment change, new environment variable, Trial reward rebalance, or new Portal combat action.

## Packaging verification
- Beta 1 → Beta 2 Bot delta: **32 changed/new, 0 deleted**; final **161 files**.
- Beta 1 → Beta 2 Web delta: **59 changed/new, 0 deleted**; final **836 files**.
- Individual Bot/Web patch reconstruction: **PASS**.
- Paired updater reconstruction: **PASS**.
- Full Bot/Web and Complete archive source-tree match: **PASS**.
- ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **10 / 10 PASS**.
