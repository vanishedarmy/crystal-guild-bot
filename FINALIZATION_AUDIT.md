# Crystal Guild v1.5.0 — Trails & Raids Alpha 6 Release Audit

## Frozen Alpha 6 contract
- Bot/Web/frontend: `1.5.0-trails-raids-a6`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Production Dungeon catalog: **4**, unchanged
- Scripted flagship Trials: **6**

## Release scope
Alpha 6 adds **Leviathan — Tidebreak Expanse** with Tidal Sweep side pressure, Undertow resource pressure, a two-round Maelstrom Stability Gauge, and stability-dependent Tidal Wave. Alpha 5's roomy collapsible Trial Board remains intact. Existing raid rewards/economy, earlier Trials, unscripted raids, and all four production Dungeons remain unchanged.

## Validation
- **568/568 Bot**, **430/430 frontend**, **47/47 hosted Web/API**.
- **104/104 Python compile**, **206/206 frontend parser**, **165/165 Node syntax**.
- **37 bosses / 4 Dungeons / 0 GameData errors**.
- Public artwork: **0 PNG / 575 WebP**; active image routes **154/154**.
- Real Alpha 5 → Alpha 6 schema-10 upgrade/recovery drill: **PASS**; Lv.17 / 4,321 Gil preserved exactly.

## Packaging verification
- Alpha 5 → Alpha 6 Bot: **31 changed/new, 0 deleted**; final **158 files**.
- Alpha 5 → Alpha 6 Web: **57 changed/new, 0 deleted**; final **833 files**.
- Full/individual/paired reconstruction: **158/158 Bot** and **833/833 Web PASS**.
- Release ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **10 / 10 PASS**.

## Deployment
Deploy matching Alpha 6 Web + Bot together. Preserve the live database, `.env`, Twitch tokens, hosted secrets, and persistent-disk state. No migration is required from Alpha 5.
