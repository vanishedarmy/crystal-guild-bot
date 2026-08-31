# Crystal Guild v1.5.0 — Trails & Raids Beta 3 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **592 / 592 PASS**.
- Frontend Node regression suite: **449 / 449 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

## Beta 3 coverage
- Two independent Bot connections queue different raiders in the same round without stale-state clobbering.
- Guarded combat mutations refresh the newest committed runtime revision after SQLite write intent is acquired.
- New Raid actions are internally scoped to the exact run and target round; action stamps remain private.
- One restored unstamped Beta 2 queued action is honored once for in-progress upgrade compatibility.
- Duplicate daemon timer snapshots are exact run/round scoped; the second stale worker no-ops and cannot advance an additional round.
- Beta 2 settlement receipts remain intact, so victory/wipe rewards continue to settle exactly once.
- Public Overlay state excludes `raid_instance_id`, internal `raid_run` stamps, and mechanic target IDs.
- The Trial & Raid Board shows a dedicated Round Readiness strip and richer Last Trial Result contributor details.
- Trial Chronicle, repeat mastery, all seven scripted Trials, unscripted raids, and all four production Dungeons remain green.

## Source / asset validation
- Python compile sweep: **108 / 108 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **210 / 210 PASS**.
- Plain JS/MJS `node --check`: **169 / 169 PASS**.
- GameData: **37 bosses / 4 Dungeons / 0 errors**.
- Public artwork: **0 PNG / 575 WebP**.
- Static literal WebP route sweep: **165 / 165 unique paths resolve**, 0 missing; route set is unchanged from Beta 2 under the same sweep.
- All **7 / 7** flagship Trial artwork routes resolve in the shipping tree.

## Upgrade / recovery drill
- Real Beta 2 schema-10 database reopened under Beta 3: **PASS**.
- Existing test-player level/Gil preserved exactly (**Lv.17 / 4,321 Gil**): **PASS**.
- No schema migration was triggered: **PASS**.
- A genuine Beta 2 runtime checkpoint restored with revision `0`: **PASS**.
- A pre-Beta-3 unstamped queued Defend was honored once after upgrade: **PASS**.
- Runtime revision advanced normally after the first Beta 3 mutation: **PASS**.
- SQLite quick-check and foreign-key check: **PASS**.
- Non-destructive backup/restore verification: **PASS**.

## Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-b3`.
- Local DB schema **10**, hosted sync **1**, Portal Action protocol **25**, Twitch prefix `!`.
- No migration, reset, OAuth/environment change, new environment variable, Trial reward rebalance, new Trial, or new Portal combat action.

## Packaging verification
- Beta 2 → Beta 3 Bot delta: **33 changed/new, 0 deleted**; final **162 files**.
- Beta 2 → Beta 3 Web delta: **59 changed/new, 0 deleted**; final **837 files**.
- Individual Bot/Web patch reconstruction: **PASS**.
- Paired updater reconstruction: **PASS**.
- Full Bot/Web and Complete archive source-tree match: **PASS**.
- ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **10 / 10 PASS**.
