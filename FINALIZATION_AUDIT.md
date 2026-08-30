# Crystal Guild v1.5.0 — Trails & Raids Alpha 5 Release Audit

## Frozen Alpha 5 contract
- Bot/Web/frontend: `1.5.0-trails-raids-a5`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Production Dungeon catalog: **4**, unchanged
- Flagship Trial catalog: **5** — Ifrit, Shiva, Ramuh, Titan, Garuda

## Release scope
Alpha 5 adds **Garuda — Eye of the Storm** with Slipstream brace pressure, Friction containment, Satin/Razor Plume adds, and variable-strength Aerial Blast. It also rebuilds the flagship Trial & Raid Board into a spacious two-column desktop presentation with wider readable copy and responsive one-column fallbacks. Existing raid rewards/economy and all four production Dungeons remain unchanged.

## Release-quality guarantees
- Existing Bot-authoritative Twitch raid actions remain unchanged; no new targeting command is introduced.
- Scripted add interception remains restart/checkpoint compatible and public Overlay add state exposes only name/HP.
- Hosted Overlay retains forbidden-private-field protection; internal add IDs never enter the public payload.
- Trial Board collapse state remains persistent with the established right-hand closed / down-hand open pointer.
- Ifrit, Shiva, Ramuh, Titan, ordinary raids, Dungeons, Fellowship, Expeditions, inventory, Jobs, and player progression remain regression-covered.

## Final validation
- **562/562 Bot**, **425/425 frontend**, **47/47 hosted Web/API**.
- **103/103 Python compile**, **205/205 JS/JSX/MJS parser**, **164/164 Node syntax**.
- **153/153** active literal image routes; **0 PNG / 575 WebP** public artwork.
- **37 bosses / 4 Dungeons / 0 GameData errors**.
- Real Alpha 4 → Alpha 5 schema-10 upgrade and non-destructive recovery drill: **PASS**; Lv.17 / 4,321 Gil preserved exactly.

## Packaging verification
- Alpha 4 → Alpha 5 Bot: **39 changed/new, 0 deleted**; final **157 files**.
- Alpha 4 → Alpha 5 Web: **58 changed/new, 0 deleted**; final **832 files**.
- Full Bot/Web, individual patch helpers, paired updater, and complete archive reconstruct the exact frozen trees: **PASS**.
- All **6/6** release ZIPs pass CRC/integrity checks; private/runtime-artifact hygiene is **0 violations**.
- SHA-256 manifest: **10/10 PASS**.

## Deployment
Deploy matching Alpha 5 Web + Bot together. Preserve the live database, `.env`, Twitch tokens, hosted secrets, and persistent-disk state. No migration is required from Alpha 4.
