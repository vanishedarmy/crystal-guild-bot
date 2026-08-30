# Crystal Guild v1.4.0 — Dungeons & Delves Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **533 / 533 PASS**.
- Frontend Node regression suite: **399 / 399 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

## Production-release coverage
- RC1 feature set promotes unchanged into the stable v1.4.0 release.
- Four-Dungeon catalog remains production frozen.
- Exact run/chamber/revision stale-state binding, cross-connection SQLite serialization, action-ID replay idempotency, and restart/reconnect persistence remain green.
- Mobile Dungeon Board disclosure remains pinned to the right edge at <=620px with right-hand closed / down-hand open.
- Player-facing What's New now presents Dungeons & Delves as a shipped stable release; prerelease milestones remain engineering history only.
- Runtime overlay state remains excluded from the shipping contract.

## Source / asset validation
- Python compile sweep across Bot + Web: **98 / 98 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **198 / 198 PASS**.
- Plain JS/MJS `node --check`: **158 / 158 PASS**.
- Active quoted literal image-route audit: **149 / 149 PASS**; **0 missing**.
- Public artwork: **0 PNG / 576 WebP**.
- GameData: **4 Dungeons / 0 errors**.

## Upgrade / recovery drill
- Real RC1-created schema-10 database upgraded in place under the production code: **PASS**.
- Existing test-player level/Gil preserved exactly (**Lv.17 / 4,321 Gil**): **PASS**.
- Non-destructive backup/restore recovery drill: **PASS**.
- SQLite quick-check, foreign keys, WAL/busy-timeout runtime pragmas, and runtime-checkpoint verification: **PASS**.

## Payload / compatibility
- Fully unlocked four-Dungeon Adventure-state payload: **15,390 bytes**.
- Headroom below the 16 KiB guardrail: **994 bytes**.
- Bot/Web/frontend runtime: `1.4.0-dungeons-delves`.
- Local DB schema **10**, hosted sync **1**, Portal protocol **25**, Twitch prefix `!`.
- No migration, reset, OAuth/environment, new environment variable, gameplay/economy, or balance change from RC1.

## Packaging verification
- RC1 → production Bot patch: **29 changed/new files, 0 deletions**; final Bot tree **152 files**.
- RC1 → production Web patch: **58 changed/new files, 0 deletions**; final Web tree **826 files**.
- Individual patch helpers reconstruct **152/152 Bot** and **826/826 Web** files exactly: **PASS**.
- Paired updater reconstructs **152/152 Bot** and **826/826 Web** files exactly: **PASS**.
- Complete archive contains exact final Bot/Web trees: **PASS**.
- All **6/6** release ZIPs pass CRC/integrity checks.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 checksum verification: **PASS**.
