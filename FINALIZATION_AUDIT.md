# Crystal Guild v1.4.0 — Dungeons & Delves Release Audit

## Frozen production contract
- Bot/Web/frontend: `1.4.0-dungeons-delves`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Dungeon catalog: **4**, production frozen

## Promotion scope
RC1 promotes to production without Dungeon content, reward, economy, combat, progression, schema, protocol, OAuth, or environment changes.

## Release-quality guarantees carried forward
- Exact run/chamber/revision stale-state protection and action-ID idempotency.
- Cross-connection SQLite write serialization before authoritative state reads.
- Restart/reconnect-safe active Dungeon state, route effects, and replay receipts.
- Mobile Dungeon disclosure right-alignment and stateful pointer behavior.
- Runtime `overlay/state.json` excluded from shipping and ignored by source control.
- Current package/project metadata reports v1.4.0.
- Public Previous major updates remains stable-release-only.

## Final validation
- **533/533 Bot**, **399/399 frontend**, **47/47 hosted Web/API**.
- **98/98 Python compile**, **198/198 JS/JSX/MJS parser**, **158/158 Node syntax**.
- **149/149** active literal image routes; **0 PNG / 576 WebP** public artwork.
- **4 Dungeons / 0 GameData errors**.
- Fully unlocked Adventure state: **15,390 bytes**, **994 bytes** under 16 KiB.
- Real RC1 → production in-place upgrade and non-destructive recovery drill: **PASS**.

## Packaging verification
- RC1 → production Bot patch: **29 changed/new, 0 deleted**; final **152 files**.
- RC1 → production Web patch: **58 changed/new, 0 deleted**; final **826 files**.
- Individual and paired patch helpers reconstruct the exact final Bot/Web trees: **PASS**.
- All **6/6** release ZIPs pass CRC/integrity checks; private/runtime-artifact hygiene is **0 violations**.
- SHA-256 checksum verification: **PASS**.

## Deployment
Deploy matching v1.4.0 Web + Bot together. Preserve live database, `.env`, Twitch tokens, hosted secrets, and persistent-disk state. No migration is required from RC1.
