# Crystal Guild v1.5.0 — Trails & Raids Alpha 3 Release Audit

## Frozen Alpha 3 contract
- Bot/Web/frontend: `1.5.0-trails-raids-a3`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Dungeon catalog: **4**, production frozen

## Release scope
Alpha 3 adds **Ramuh — Judgment Spire**, chain/shared-hit/Grounding mechanics, and the collapsible Trial & Raid Board. It does not rebalance existing rewards/economy or replace Alpha 1 Ifrit / Alpha 2 Shiva behavior.

## Safety guarantees carried forward
- Bot-authoritative timed Raid actions and autonomous encounter-daemon ownership.
- Persistent/restart-safe active Raid checkpoint state.
- Ramuh uses the existing action surface: `Defend` participates in Levinshare and Grounding without a new targeting command.
- Existing Dungeon run/chamber/revision stale-state binding and action replay idempotency remain intact.
- Hosted Overlay remains display-only and retains private-field rejection.
- Existing player progression is preserved; no schema migration is introduced.

## Final validation
- **550/550 Bot**, **415/415 frontend**, **47/47 hosted Web/API**.
- **101/101 Python compile**, **203/203 JS/JSX/MJS parser**, **162/162 Node syntax**.
- **151/151** active literal image routes; **0 PNG / 575 WebP** public artwork.
- **37 bosses / 4 Dungeons / 0 GameData errors**.
- Real Alpha 2 → Alpha 3 schema-10 upgrade and recovery drill: **PASS**; Lv.17 / 4,321 Gil preserved exactly.

## Packaging verification
- Alpha 2 → Alpha 3 Bot: **31 changed/new, 0 deleted**; final **155 files**.
- Alpha 2 → Alpha 3 Web: **56 changed/new, 0 deleted**; final **830 files**.
- Full and patch reconstruction: **155/155 Bot** and **830/830 Web PASS** for individual and paired update paths.
- ZIP CRC/integrity: **6 / 6 release ZIPs PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **PASS**.

## Deployment
Deploy matching Alpha 3 Web + Bot together. Preserve the live database, `.env`, Twitch tokens, hosted secrets, and persistent-disk state. No migration is required from Alpha 2.
