# Crystal Guild v1.3.0 — Guild Expansion Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **486 / 486 PASS**.
- Frontend Node regression suite: **358 / 358 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

The Bot suite includes intentional simulated acknowledgement loss, Twitch/live-status outages, corrupt checkpoint recovery, restart recovery, database recovery drills, and synthetic stress scenarios. Those warning/error log lines are expected test fixtures and are not release failures.

## Final-release coverage
- Runtime/public identity is consistently `1.3.0-guild-expansion` across Bot, hosted Web, frontend, Guide metadata, scene manifest, Windows control panel, package manifests, and current release documentation.
- Player-facing What's New now starts with **v1.3.0 · Guild Expansion**.
- **Previous major updates** contains shipped releases only: v1.2.0 Expeditions and stable v1.1/v1.0 releases. Public Alpha, Beta, and RC entries are removed.
- A frontend regression guard explicitly fails if an Alpha/Beta/RC release name is reintroduced into the public update feed.
- Hosting Guide and Portal Actions Setup now report the final runtime, local schema **9**, hosted sync schema **1**, and Portal Action protocol **22**.
- Fellowship/Airship restart persistence, simultaneous-contribution safety, stale-tab protection, replay safety, project switching, concurrent Airship launches, and exact-once return settlement remain covered.

## Source and asset validation
- Python source compilation: **90 / 90 PASS** across final Bot + Web source trees.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **184 / 184 PASS**.
- Plain JS/MJS `node --check`: **146 / 146 PASS**.
- Explicit literal image/font route audit: **145 / 145 PASS** with **0 missing**. Dynamic template routes remain covered by the existing artwork regression suites.

## Continuity
- Guild economy/progression values are unchanged from RC2.
- Fellowship UX/mobile layout is unchanged from RC2.
- Shared-state hardening is unchanged from RC2.
- Founding Hall portrait, scenic artwork, and collapsible Equipment/Inventory categories remain intact.
- Local DB schema: **9** unchanged.
- Hosted sync schema: **1** unchanged.
- Portal Action protocol: **22** unchanged.
- Twitch prefix: `!`.
- Database migration from RC2: **none**.
- Player reset: **none**.
- OAuth change: **none**.
- New environment variables: **none**.

## Final package verification
- RC2 Bot → final Bot patch: **14 changed/current files, 0 deletions**; reconstructs **147 / 147** final Bot files exactly.
- RC2 Web → final Web patch: **42 changed/current files, 0 deletions**; reconstructs **806 / 806** final Web files exactly.
- ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations** across all release archives.
- SHA-256 checksum verification: **PASS**.
