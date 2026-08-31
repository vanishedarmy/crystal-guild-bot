# Crystal Guild v1.5.1 — Relic Arsenal Complete Release Audit

## Frozen scope
- Completes Relic coverage from 8/18 to **18/18 Jobs**.
- Adds **10 Relic questlines**, **30 stage items**, and **30 matching WebP stage artworks**.
- Preserves the established three-stage Relic progression/economy.
- Keeps Hunt scenic artwork through the completed result state.
- Carries v1.5.0 Trails & Raids and Web Hotfix 4 behavior forward unchanged otherwise.

## Frozen contract
Runtime `1.5.1-relic-arsenal-complete`; local DB schema 10; hosted sync 1; Portal Action protocol 25; Twitch prefix `!`.

No migration, reset, OAuth/environment change, new variable, Trial/Raid content change, reward rebalance, or new Portal combat action.

## Validation
601/601 Bot, 469/469 frontend, 47/47 hosted; 110/110 Python compile; 214/214 frontend parser; 173/173 Node syntax; 0 CSS parse errors; 18/18 Relics; 435 items; 611/611 WebP decode; 0 PNG.

The local `npm run build` gate was attempted but Vite is not installed in this source-only container; this limitation is explicitly recorded rather than represented as a pass.

## Package verification
Final release engineering verifies exact reconstruction from the official v1.5.0 Bot + Web Hotfix 4 baselines: **164/164 Bot files** and **877/877 Web files**, **6/6 ZIP CRC**, **0 runtime/private-artifact hygiene violations**, and **10/10 SHA-256 entries**.
