# Crystal Guild v1.4.0 — Dungeons & Delves RC1 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **529 / 529 PASS**.
- Frontend Node regression suite: **396 / 396 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

## RC1 release-candidate coverage
- Four-Dungeon catalog remains feature frozen.
- Beta 3 cross-connection serialization, exact run/chamber/revision stale-state binding, action-ID replay idempotency, and restart/reconnect persistence remain green.
- Mobile Dungeon Board disclosure remains pinned to the right edge at <=620px with right-hand closed / down-hand open.
- Player-facing Previous major updates remains stable-release-only while What's New identifies RC1.
- Python project package metadata reports v1.4.0.
- Current setup, Render, maintenance, stress-test, Twitch authorization, and migration-helper labels no longer advertise stale v1.1-era releases.
- Generated `overlay/state.json` and legacy Hotfix 4 release-note debris are removed from the RC1 Bot shipping tree.

## Source / asset validation
- Python compile sweep across Bot + Web: **97 / 97 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **197 / 197 PASS**.
- Plain JS/MJS `node --check`: **157 / 157 PASS**.
- Active quoted literal image-route audit: **149 routes / 0 missing**.
- Public artwork: **0 PNG / 576 WebP**.
- GameData: **4 Dungeons / 0 errors**.

## Upgrade / recovery drill
- RC1 in-place upgrade check against an existing schema-10 database: **PASS**.
- Existing player level/Gil preserved after the check: **PASS**.
- Non-destructive backup/restore recovery drill: **PASS**.
- SQLite quick-check, foreign keys, WAL/busy-timeout runtime pragmas, and recovery checkpoint checks: **PASS**.

## Payload / compatibility
- Adventure state with all four Dungeons unlocked: **15,368 bytes**, **1,016 bytes** below the 16 KiB guardrail.
- Bot/Web/frontend: `1.4.0-dungeons-rc1`.
- Local DB schema **10**, hosted sync **1**, Portal protocol **25**, Twitch prefix `!`.
- No migration, reset, OAuth/environment, new environment variable, gameplay/economy, or balance change.

## Packaging verification
- Beta 3 → RC1 Bot patch: **30 changed/new files, 3 deletions**; final Bot tree **151 files**.
- Beta 3 → RC1 Web patch: **57 changed/new files, 0 deletions**; final Web tree **825 files**.
- Individual patch helpers and paired updater reproduce the exact final shipping trees.
- All **6 / 6** release ZIPs pass CRC/integrity checks.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **PASS**.
