# Crystal Guild v1.4.0 — Dungeons & Delves Alpha 1 Release Audit

## Scope
Foundation pass for persistent multi-room Dungeons on the verified v1.3.1 Asset Optimization baseline.

## Current-package identity
- Bot runtime: `1.4.0-dungeons-a1`
- Hosted Web/runtime: `1.4.0-dungeons-a1`
- Frontend asset revision: `1.4.0-dungeons-a1`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **23**
- Twitch prefix: `!`

## Audit targets
- Additive schema-9 → schema-10 Dungeon migration preserves existing data and verifies a pre-schema-10 backup.
- Persistent Dungeon state survives restart and supports safe retreat/defeat/completion settlement.
- Portal Dungeon actions use replay-safe Adventure mutation handling and are bound to the exact run/chamber shown by the submitting tab, so stale tabs fail closed.
- Existing v1.3 Guild Expansion, v1.2 Expeditions, assets, and UI4 behavior remain regression-covered.
- Public Previous major updates remains stable-release-only; Alpha 1 appears only as the current What's New entry.
- No player reset, OAuth change, or new environment variable is introduced.

## Result
**PASS** — source/runtime validation complete; final archive reconstruction, CRC, hygiene, and checksums are verified during packaging.
