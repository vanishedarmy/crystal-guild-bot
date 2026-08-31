# Crystal Guild v1.5.0 — Trails & Raids Alpha 7 Release Audit

## Frozen Alpha 7 contract
- Bot/Web/frontend: `1.5.0-trails-raids-a7`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Production Dungeon catalog: **4**, unchanged
- Scripted flagship Trials: **7** (six elemental Trials + Bahamut capstone)

## Release scope
Alpha 7 adds **Bahamut — The Final Coil** with Flare Breath, Akh Morn, Megaflare Towers, and a critical-HP Teraflare damage race. Bahamut receives a full-width capstone card while the existing roomy collapsible Trial Board remains intact. Existing raid rewards/economy, earlier Trials, unscripted raids, and all four production Dungeons remain unchanged.

## Validation
- **574/574 Bot**, **435/435 frontend**, **47/47 hosted Web/API**.
- **105/105 Python compile**, **207/207 frontend parser**, **166/166 Node syntax**.
- **37 bosses / 4 Dungeons / 0 GameData errors**.
- Public artwork: **0 PNG / 575 WebP**; literal image routes **165/165**.
- Real Alpha 6 → Alpha 7 schema-10 upgrade/recovery drill: **PASS**; Lv.17 / 4,321 Gil preserved exactly.

## Packaging verification
- Alpha 6 → Alpha 7 Bot: **31 changed/new, 0 deleted**; final **159 files**.
- Alpha 6 → Alpha 7 Web: **58 changed/new, 0 deleted**; final **834 files**.
- Full/individual/paired reconstruction: **159/159 Bot** and **834/834 Web PASS**.
- Release ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **10 / 10 PASS**.

## Deployment
Deploy matching Alpha 7 Web + Bot together. Preserve the live database, `.env`, Twitch tokens, hosted secrets, and persistent-disk state. No migration is required from Alpha 6.
