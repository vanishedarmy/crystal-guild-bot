# Crystal Guild v1.5.0 — Trails & Raids Alpha 2 Release Audit

## Frozen Alpha 2 contract
- Bot/Web/frontend: `1.5.0-trails-raids-a2`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Dungeon catalog: **4**, unchanged

## Release scope
Alpha 2 adds Shiva — Diamond Throne, persistent encounter adds, a shared Break gauge, Stagger windows, and role-aware raid contribution presentation. It does not rebalance existing rewards/economy or replace Alpha 1 Ifrit behavior.

## Safety guarantees carried forward
- Bot-authoritative timed Raid actions and autonomous encounter daemon ownership.
- Persistent/restart-safe active raid checkpoint state.
- Existing Dungeon run/chamber/revision stale-state binding and action replay idempotency.
- Hosted Overlay remains display-only and rejects forbidden private fields.
- Existing player progression is preserved; no schema migration is introduced.

## Final validation
- **545/545 Bot**, **410/410 frontend**, **47/47 hosted Web/API**.
- **100/100 Python compile**, **202/202 JS/JSX/MJS parser**, **161/161 Node syntax**.
- **37 bosses / 4 Dungeons / 0 GameData errors**; **0 PNG / 575 WebP**.
- Real v1.4.0 → Alpha 2 in-place schema-10 upgrade and recovery drill: **PASS**; Lv.17 / 4,321 Gil preserved exactly.

## Packaging verification
- Source-delta counts: Alpha 1 → Alpha 2 Bot: 32 changed/new, 0 deleted; final 154 files. Alpha 1 Hotfix 2 → Alpha 2 Web: 55 changed/new, 0 deleted; final 829 files.
- Full and patch reconstruction: Full archives and individual/paired patch helpers reconstruct the exact frozen Alpha 2 trees: 154/154 Bot and 829/829 Web PASS.
- ZIP CRC/integrity: **6 / 6 release ZIPs PASS**
- Runtime/private-artifact hygiene: **0 violations**
- SHA-256 verification: **PASS**.

## Deployment
Deploy matching Alpha 2 Web + Bot together. Preserve live database, `.env`, Twitch tokens, hosted secrets, and persistent-disk state.
