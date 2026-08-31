# Crystal Guild v1.5.0 — Trails & Raids Beta 3 Release Audit

## Frozen Beta 3 contract
- Bot/Web/frontend: `1.5.0-trails-raids-b3`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Scripted flagship Trials: **7**, content frozen
- Production Dungeons: **4**, unchanged

## Scope
Beta 3 hardens active Raid state across simultaneous/reconnected Bot connections and improves live/result readability. It does not add another Trial, currency, reward multiplier, database table, Portal mutation, or economy/combat rebalance.

## Release-quality guarantees
- Guarded combat writes serialize through SQLite write intent and refresh the newest committed runtime revision before mutation.
- Different connections can queue different raiders in the same round without overwriting one another.
- New Raid actions are exact run/round scoped; one restored unstamped Beta 2 action is honored once for compatibility.
- Timer workers resolve only the exact Raid run/round snapshot they observed; a stale duplicate tick silently no-ops.
- Beta 2 bounded settlement receipts continue preventing duplicate victory/wipe settlement after combat ends.
- Public Overlay state does not expose exact run IDs, action stamps, or internal mechanic target IDs.
- Raid combat remains Twitch/Bot-authoritative; Portal Chronicle/result surfaces remain read-only.
- The Board's Round Readiness strip and richer Last Trial Result are presentation-only and do not alter rewards or Chronicle math.
- Existing Dungeon stale-state/replay protections and all seven scripted Trial combat systems remain regression-covered.

## Final validation
- **592/592 Bot**, **449/449 frontend**, **47/47 hosted Web/API**.
- **108/108 Python compile**, **210/210 JS/JSX/MJS parser**, **169/169 Node syntax**.
- **165/165** unique static literal WebP paths resolve; route set unchanged from Beta 2 under the same sweep.
- **7/7** flagship Trial art routes resolve; public artwork remains **0 PNG / 575 WebP**.
- **37 bosses / 4 Dungeons / 0 GameData errors**.
- Real Beta 2 → Beta 3 schema-10 in-place upgrade and non-destructive recovery drill: **PASS**.
- Existing test-player level/Gil preserved exactly at **Lv.17 / 4,321 Gil**.
- Pre-Beta-3 unstamped queued-action compatibility: **PASS**.

## Packaging verification
- Beta 2 → Beta 3 Bot patch: **33 changed/new, 0 deleted**; final **162 files**.
- Beta 2 → Beta 3 Web patch: **59 changed/new, 0 deleted**; final **837 files**.
- Individual and paired patch helpers reconstruct the exact final Bot/Web trees: **PASS**.
- Full Bot/Web and Complete archives match the frozen source trees: **PASS**.
- All **6/6** ZIPs pass CRC/integrity; private/runtime-artifact hygiene is **0 violations**; SHA-256 verification is **10/10 PASS**.

## Deployment
Deploy matching Beta 3 Web + Bot together. Preserve the live database, `.env`, Twitch tokens, hosted secrets, and persistent-disk state. No migration or reset is required from Beta 2.
