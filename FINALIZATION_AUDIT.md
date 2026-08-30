# Crystal Guild v1.5.0 — Trails & Raids Alpha 4 Release Audit

## Frozen Alpha 4 contract
- Bot/Web/frontend: `1.5.0-trails-raids-a4`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Dungeon catalog: **4**, production frozen

## Release scope
Alpha 4 adds **Titan — Heart of the Crag**, Landslide response, Granite Gaol restraint/rescue, a two-round Heart damage check, and weakened/empowered Earthen Fury resolution. The Alpha 3 collapsible Trial & Raid Board remains intact. Existing rewards/economy are not rebalanced and Ifrit/Shiva/Ramuh behavior is carried forward.

## Safety guarantees carried forward
- Bot-authoritative timed Raid actions and autonomous encounter-daemon ownership.
- Persistent/restart-safe active Raid checkpoint state.
- Titan uses the existing action surface: Defend responds to Landslide and existing boss-directed attacks automatically hit active Gaol/Heart mechanic adds.
- Restrained-raider state is held inside the existing raid checkpoint and is cleared precisely when the matching Gaol is destroyed.
- Hosted Overlay remains display-only and strips internal target/release identifiers.
- Existing Dungeon run/chamber/revision stale-state binding and action replay idempotency remain intact.
- Existing player progression is preserved; no schema migration is introduced.

## Final validation
- **556/556 Bot**, **420/420 frontend**, **47/47 hosted Web/API**.
- **102/102 Python compile**, **204/204 JS/JSX/MJS parser**, **163/163 Node syntax**.
- **152/152** active literal image routes; **0 PNG / 575 WebP** public artwork.
- **37 bosses / 4 Dungeons / 0 GameData errors**.
- Real Alpha 3 → Alpha 4 schema-10 upgrade and recovery drill: **PASS**; Lv.17 / 4,321 Gil preserved exactly.

## Packaging verification
- Alpha 3 → Alpha 4 Bot: **32 changed/new, 0 deleted**; final **156 files**.
- Alpha 3 → Alpha 4 Web: **57 changed/new, 0 deleted**; final **831 files**.
- Full and patch reconstruction: **156/156 Bot** and **831/831 Web PASS** for individual and paired update paths.
- ZIP CRC/integrity: **6 / 6 release ZIPs PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **PASS**.

## Deployment
Deploy matching Alpha 4 Web + Bot together. Preserve the live database, `.env`, Twitch tokens, hosted secrets, and persistent-disk state. No migration is required from Alpha 3.
