# Crystal Guild v1.5.0 — Trails & Raids RC1 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **598 / 598 PASS**.
- Frontend Node regression suite: **452 / 452 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

## RC1 coverage
- Round Readiness and all-actions-ready decisions count only actions owned by the exact active Raid run and upcoming round.
- A stale prior-round action is excluded from readiness and cannot falsely complete the party-ready state.
- A wrong-run action is excluded from readiness.
- Malformed `raid_round` stamps fail closed rather than raising; normal round resolution safely substitutes the established automatic Attack.
- Current exact run/round actions remain ready and resolve normally.
- One unstamped pre-Beta-3 restored queued action remains accepted once for in-progress upgrade compatibility.
- Beta 3 shared-state revision reconciliation, cross-connection queue merging, and exact timer-tick stale-state protection remain green.
- Beta 2 exactly-once settlement receipts remain green.
- Trial Chronicle, repeat mastery, all seven scripted Trials, unscripted raids, and all four production Dungeons remain green.

## Source / asset validation
- Python compile sweep: **109 / 109 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **211 / 211 PASS**.
- Plain JS/MJS `node --check`: **170 / 170 PASS**.
- GameData: **37 bosses / 4 Dungeons / 0 errors**.
- Public artwork: **0 PNG / 575 WebP**.
- WebP decode verification: **575 / 575 PASS**.
- Literal WebP token set is unchanged from the Beta 3 source tree: **730 / 730 identical tokens**, 0 added / 0 removed.
- Beta 3's previously audited **165 / 165** static literal image-route set is therefore unchanged in RC1.
- All **7 / 7** flagship Trial artwork routes resolve in the shipping tree.

## Upgrade / recovery drill
- Genuine Beta 3 schema-10 database/checkpoint reopened under RC1: **PASS**.
- Existing test-player level/Gil preserved exactly (**Lv.17 / 4,321 Gil**): **PASS**.
- No schema migration was triggered: **PASS**.
- A Beta 3 exact run/round queued Defend survived the upgrade and counted ready for its intended upcoming round: **PASS**.
- First RC1 guarded mutation advanced the combat revision normally: **PASS**.
- SQLite quick-check and foreign-key check: **PASS**.
- Non-destructive backup/restore verification: **PASS**.

## Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-rc1`.
- Local DB schema **10**, hosted sync **1**, Portal Action protocol **25**, Twitch prefix `!`.
- No migration, reset, OAuth/environment change, new environment variable, Trial reward rebalance, new Trial, or new Portal combat action.

## Packaging verification
- Beta 3 → RC1 Bot delta: **33 changed/new, 0 deleted**; final **163 files**.
- Beta 3 → RC1 Web delta: **55 changed/new, 0 deleted**; final **838 files**.
- Individual Bot/Web patch reconstruction: **PASS**.
- Paired updater reconstruction: **PASS**.
- Full Bot/Web and Complete archive source-tree match: **PASS**.
- ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **10 / 10 PASS**.
