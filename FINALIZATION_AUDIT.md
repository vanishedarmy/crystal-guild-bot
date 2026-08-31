# Crystal Guild v1.5.0 — Trails & Raids Beta 1 Release Audit

## Frozen Beta 1 contract
- Bot/Web/frontend: `1.5.0-trails-raids-b1`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Scripted flagship Trials: **7**, content frozen
- Production Dungeons: **4**, unchanged

## Scope
Beta 1 consolidates the seven Alpha Trials into durable personal progression records. It adds the Trial Chronicle, personal bests, and mastery presentation without changing Trial rewards, encounter mechanics, unscripted raids, Dungeon progression, or the economy.

Existing Trial clears are inherited from the authoritative boss-clear ledger. Metrics that did not exist during Alpha—tracked wipes, fastest clear rounds, and contribution bests—begin recording from Beta 1 onward rather than being guessed retroactively.

## Release-quality guarantees
- Trial metrics use the existing schema-10 generic record-stat store; no migration is introduced.
- Unscripted raids remain excluded from Trial Chronicle metrics.
- Raid combat remains Twitch/Bot-authoritative; Chronicle surfaces are read-only Portal presentation.
- Existing exact Dungeon stale-state/replay protections and all seven scripted Trial combat systems remain regression-covered.
- Alpha 7 → Beta 1 upgrade/recovery preserves existing player data exactly.

## Final validation
- **580/580 Bot**, **440/440 frontend**, **47/47 hosted Web/API**.
- **106/106 Python compile**, **208/208 JS/JSX/MJS parser**, **167/167 Node syntax**.
- **155/155** unique static literal image paths resolve; route set unchanged from Alpha 7.
- **7/7** flagship Trial art routes resolve; public artwork remains **0 PNG / 575 WebP**.
- **37 bosses / 4 Dungeons / 0 GameData errors**.
- Real Alpha 7 → Beta 1 schema-10 in-place upgrade and non-destructive recovery drill: **PASS**.

## Packaging verification
- Alpha 7 → Beta 1 Bot patch: **31 changed/new, 0 deleted**; final **160 files**.
- Alpha 7 → Beta 1 Web patch: **59 changed/new, 0 deleted**; final **835 files**.
- Individual and paired patch helpers reconstruct the exact final Bot/Web trees: **PASS**.
- Full Bot/Web and Complete archives match the frozen source trees: **PASS**.
- All **6/6** release ZIPs pass CRC/integrity checks; private/runtime-artifact hygiene is **0 violations**.
- SHA-256 checksum verification: **10/10 PASS**.

## Deployment
Deploy matching Beta 1 Web + Bot together. Preserve the live database, `.env`, Twitch tokens, hosted secrets, and persistent-disk state. No migration or reset is required from Alpha 7.
