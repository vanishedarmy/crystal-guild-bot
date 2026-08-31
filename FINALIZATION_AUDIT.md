# Crystal Guild v1.5.0 — Trails & Raids Beta 2 Release Audit

## Frozen Beta 2 contract
- Bot/Web/frontend: `1.5.0-trails-raids-b2`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Scripted flagship Trials: **7**, content frozen
- Production Dungeons: **4**, unchanged

## Scope
Beta 2 adds repeat-clear mastery, Last Trial Result presentation, live action-readiness counts, and exactly-once Raid settlement hardening. It does not add another Trial, currency, reward multiplier, database table, Portal mutation, or economy/combat rebalance.

## Release-quality guarantees
- Repeat mastery is derived from the existing authoritative clear ledger and is retroactive without data conversion.
- Beta 1 Trial Chronicle records remain authoritative and are not recomputed or reset.
- Exact Raid run identities and bounded atomic settlement receipts prevent stale/recovered connections from granting the same run twice.
- Restored pre-Beta-2 active raids receive a stable compatibility identity without migration.
- Duplicate settlement replay reloads authoritative runtime state rather than clearing or overwriting a newer run.
- Public Overlay state exposes only sanitized readiness counts; private run IDs and internal target IDs remain Bot-side.
- Raid combat remains Twitch/Bot-authoritative; Portal Chronicle/result surfaces remain read-only.
- Existing Dungeon stale-state/replay protections and all seven scripted Trial combat systems remain regression-covered.

## Final validation
- **586/586 Bot**, **445/445 frontend**, **47/47 hosted Web/API**.
- **107/107 Python compile**, **209/209 JS/JSX/MJS parser**, **168/168 Node syntax**.
- **155/155** unique static literal image paths resolve; route set unchanged from Beta 1.
- **7/7** flagship Trial art routes resolve; public artwork remains **0 PNG / 575 WebP**.
- **37 bosses / 4 Dungeons / 0 GameData errors**.
- Real Beta 1 → Beta 2 schema-10 in-place upgrade and non-destructive recovery drill: **PASS**.
- Existing test-player level/Gil preserved exactly at **Lv.17 / 4,321 Gil**.

## Packaging verification
- Beta 1 → Beta 2 Bot patch: **32 changed/new, 0 deleted**; final **161 files**.
- Beta 1 → Beta 2 Web patch: **59 changed/new, 0 deleted**; final **836 files**.
- Individual and paired patch helpers reconstruct the exact final Bot/Web trees: **PASS**.
- Full Bot/Web and Complete archives match the frozen source trees: **PASS**.
- All **6/6** release ZIPs pass CRC/integrity checks; private/runtime-artifact hygiene is **0 violations**.
- SHA-256 verification: **10/10 PASS**.

## Deployment
Deploy matching Beta 2 Web + Bot together. Preserve the live database, `.env`, Twitch tokens, hosted secrets, and persistent-disk state. No migration or reset is required from Beta 1.
