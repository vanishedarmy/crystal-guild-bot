# Crystal Guild v1.5.0 — Trails & Raids Alpha 1 Release Audit

## Frozen Alpha 1 contract
- Bot/Web/frontend: `1.5.0-trails-raids-a1`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- v1.4 Dungeon catalog: **4**, unchanged/frozen

## Feature boundary
Alpha 1 introduces the Raid Combat Engine scripting/presentation foundation and one flagship Trial, **Ifrit — Inferno Crucible**. Raid participation remains Twitch/Bot-authoritative; the new Portal Raid Board is read-only.

## Release-quality guarantees
- Telegraph state and damage-check resolution are Bot-authoritative.
- Public raid sync strips Twitch IDs and internal target IDs.
- Existing raid recovery, Limit Break, Summon, revive, phase, and enrage paths remain regression-covered.
- Existing v1.4 Dungeon persistence, stale-state binding, replay idempotency, and frozen content remain untouched.
- Upgrade is non-destructive and requires no schema migration.

## Final validation
- **539/539 Bot**, **404/404 frontend**, **47/47 hosted Web/API**.
- **99/99 Python**, **200/200 parser**, **159/159 Node syntax**.
- **150/150** active quoted literal image routes; **0 PNG / 576 WebP** public artwork.
- **37 bosses / 4 Dungeons / 0 GameData errors**.
- Real v1.4.0 → Alpha 1 in-place upgrade and recovery drill: **PASS**; Lv.17 / 4,321 Gil preserved exactly.

## Packaging verification
- v1.4.0 → Alpha 1 Bot patch: **34 changed/new, 0 deleted**; final **153 files**.
- v1.4.0 → Alpha 1 Web patch: **58 changed/new, 0 deleted**; final **828 files**.
- Individual and paired patch helpers reconstruct exact final Bot/Web trees: **PASS**.
- All **6/6** release ZIPs pass CRC/integrity checks; private/runtime-artifact hygiene is **0 violations**.
- SHA-256 checksum verification: **PASS**.
