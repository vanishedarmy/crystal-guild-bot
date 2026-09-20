# Crystal Guild v1.9.0 Alpha 2 — Economy Balance Upgrade Guide

## Upgrade from v1.9.0 Alpha 1 — Moogle Trading Post

Replace the matching **Bot and Web packages together**, preserving the live database, `.env`, Twitch token storage, hosted secrets, and persistent data.

No database migration occurs in Alpha 2. Schema remains **19** and existing Trading Post listings/player progress are preserved.

## Release contract
- Runtime/frontend: `1.9.0-economy-balance-alpha2`
- Local database schema: **19**
- Hosted sync schema: **1**
- Portal Action protocol: **36**

## Gameplay changes
- Mineral Survey: 850 Gil / 1,050 focused.
- Specialist Acquisition: 1,850 Gil / 2,300 focused.
- Press Adamantite: 1,600 Gil.
- Trading Post: 15 Ventures rather than 15 Expeditions.
- Monster Toss payouts: 10 / 15 / 30 / 50 / 80 / 120 MGP.

No other general reward curve is reduced.
