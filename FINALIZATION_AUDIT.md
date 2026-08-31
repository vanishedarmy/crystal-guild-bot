# Crystal Guild v1.5.0 — Trails & Raids RC1 Release Audit

## Frozen RC1 contract
- Bot/Web/frontend: `1.5.0-trails-raids-rc1`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Scripted flagship Trials: **7**, content frozen
- Production Dungeons: **4**, unchanged

## Scope
RC1 is a release-candidate hardening and metadata cleanup pass. It adds no Trial, currency, reward multiplier, database table, Portal combat mutation, or economy/combat rebalance.

## Release-quality guarantees
- Readiness presentation and all-actions-ready decisions use exact active-run/upcoming-round ownership.
- Stale prior-round and wrong-run actions do not count toward readiness.
- Malformed stamped actions fail closed and fall back to the normal automatic Attack instead of breaking round resolution.
- One unstamped pre-Beta-3 restored queued action remains accepted once for upgrade compatibility.
- Beta 3 authoritative cross-connection revisions and exact timer-tick stale-state binding remain intact.
- Beta 2 bounded exactly-once settlement receipts remain intact.
- Public Overlay state still excludes exact run IDs, action stamps, and internal mechanic target IDs.
- Raid combat remains Twitch/Bot-authoritative and the Portal remains read-only for Raid combat.
- Existing Dungeon stale-state/replay protections and all seven scripted Trial combat systems remain regression-covered.
- Current release identity is consistent across Bot control panel, Bot/Web package metadata, hosted health, frontend cache revision, What's New, and Player Guide.

## Final validation
- **598/598 Bot**, **452/452 frontend**, **47/47 hosted Web/API**.
- **109/109 Python compile**, **211/211 JS/JSX/MJS parser**, **170/170 Node syntax**.
- **575/575 WebP** assets decode; route-token set is unchanged from Beta 3 and all **7/7** flagship Trial art routes resolve.
- **37 bosses / 4 Dungeons / 0 GameData errors**.
- Real Beta 3 → RC1 schema-10 in-place upgrade and non-destructive recovery drill: **PASS**.
- Existing test-player level/Gil preserved exactly at **Lv.17 / 4,321 Gil**.
- Beta 3 exact run/round queued-action restoration under RC1 readiness: **PASS**.

## Packaging verification
- Beta 3 → RC1 Bot patch: **33 changed/new, 0 deleted**; final **163 files**.
- Beta 3 → RC1 Web patch: **55 changed/new, 0 deleted**; final **838 files**.
- Individual and paired patch helpers reconstruct the exact final Bot/Web trees: **PASS**.
- Full Bot/Web and Complete archives match the frozen source trees: **PASS**.
- All **6/6** ZIPs pass CRC/integrity; private/runtime-artifact hygiene is **0 violations**; SHA-256 verification is **10/10 PASS**.

## Deployment
Deploy matching RC1 Web + Bot together. Preserve the live database, `.env`, Twitch tokens, hosted secrets, and persistent-disk state. No migration or reset is required from Beta 3.
