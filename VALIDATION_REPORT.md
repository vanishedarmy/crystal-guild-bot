# Crystal Guild v1.3.0 — Guild Expansion RC1 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **485 / 485 PASS**.
- Frontend Node regression suite: **357 / 357 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.
- Focused RC1 finalization/migration suite: **4 / 4 PASS**.

The Bot suite includes intentional simulated acknowledgement loss, Twitch/live-status outages, corrupt checkpoint recovery, restart recovery, database recovery drills, and synthetic stress scenarios. Those warning/error log lines are expected test fixtures and are not RC1 failures.

## RC1 finalization coverage
- Runtime/public identity is consistently `1.3.0-guild-expansion-rc1` across Bot, hosted Web, frontend, Guide metadata, scene manifest, Windows control panel, and release docs.
- The stale Windows control-panel Beta banner/release assertion is removed.
- Player Guide Fellowship content remains player-facing and excludes release-engineering/database jargon.
- Expedition unlock terminology now matches the v1.3 major-facility Board: **Fellowship LVL 6 + Guild Hall Lv. 1**.
- Fellowship/Airship state survives database/engine restart.
- The additive schema-8 → schema-9 Airship migration preserves existing player/Guild progress, creates the verified pre-schema-9 backup, and passes database quick-check.
- Beta 3 simultaneous-contribution, stale-tab, replay, project-switch, concurrent Airship launch, and exact-once return settlement protections remain covered.
- Release recovery drill and synthetic stress/integrity guardrails remain covered by the full Bot suite.

## Source validation
- Python source compilation: **90 / 90 PASS** across RC1 Bot + Web source trees.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **182 / 182 PASS**.
- Plain JS/MJS `node --check`: **146 / 146 PASS**.
- Explicit literal image/font route audit: **145 routes checked / 0 missing**. Dynamic template routes remain covered by the existing artwork regression suites.

## Continuity
- Beta 1 Guild economy tuning remains unchanged.
- Beta 2 Fellowship UX/mobile consolidation remains unchanged.
- Beta 3 shared-state hardening remains unchanged.
- Founding Hall portrait and collapsible Equipment/Inventory categories remain intact.
- Local DB schema: **9** unchanged from Beta 3.
- Hosted sync schema: **1** unchanged.
- Portal Action protocol: **22** unchanged from Beta 3.
- Twitch prefix: `!`.
- Database migration from Beta 3: **none**.
- Player reset: **none**.
- OAuth change: **none**.
- New environment variables: **none**.

## Final package verification
- Beta 3 Bot → RC1 Bot patch: **13 changed/new files, 0 deletions**; reconstructs **147 / 147** final Bot files exactly.
- Beta 3 Web → RC1 Web patch: **37 changed/new files, 0 deletions**; reconstructs **806 / 806** final Web files exactly.
- ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations** across all release archives.
- SHA-256 checksum verification: **PASS**.
