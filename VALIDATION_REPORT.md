# Crystal Guild v1.3.0 — Guild Expansion Beta 3 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **482 / 482 PASS**.
- Frontend Node regression suite: **354 / 354 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.
- Focused Beta 3 shared-state hardening suite: **7 / 7 PASS** (included in Bot total).

The Bot log includes intentional simulated acknowledgement loss, temporary Twitch/live-status failures, and runtime-checkpoint recovery cases. Those scenarios pass and are not Beta 3 failures.

## Beta 3 hardening coverage
- Simultaneous Guild contributions recompute the live remaining requirement under the serialized Guild mutation lock, preventing overfill and excess resource deduction.
- Near-simultaneous executions of the same Portal action ID re-check replay state after obtaining the write lock and mutate Fellowship state once.
- Fellowship contribution actions carry the project ID the player actually had open. If the streamer has changed projects, the stale action fails closed instead of donating to the replacement project.
- Project selection and project-completion finalization are serialized so facility/reward settlement cannot split from the completed requirement.
- Concurrent Airship mission launch requests create only one active run.
- Due Airship missions survive restart/reconnect, settle exactly once, and cannot duplicate contributor rewards.
- Airship settlement cleanup is scoped to the exact active run ID so stale work cannot clear a newer mission.

## Source validation
- Python source compilation: **89 / 89 PASS** across Beta 3 Web + Bot source trees.
- Frontend JS/JSX TypeScript-parser sweep: **67 / 67 PASS**.
- Plain JS/MJS `node --check`: **145 / 145 PASS**.
- Explicit literal image/font route audit: **145 routes checked / 0 missing**. Dynamic template routes are covered by the existing frontend artwork regression suites.

## Continuity
- Beta 1 Guild economy tuning remains unchanged.
- Beta 2 Fellowship UX/mobile consolidation remains unchanged.
- Alpha 5 Hotfix 1 Founding Hall portrait and collapsible Equipment inventory groups remain intact.
- Local DB schema: **9** unchanged.
- Hosted sync schema: **1** unchanged.
- Portal Action protocol: **22** (advanced from 21 only for project-bound Fellowship contribution safety).
- Twitch prefix: `!`.
- Database migration: **none**.
- Player reset: **none**.
- OAuth change: **none**.
- New environment variables: **none**.

## Final package verification
- Beta 1 Bot → Beta 3 Bot patch: **21 changed/new files, 0 deletions**; reconstructs **146 / 146** final Bot files exactly.
- Beta 2 Web → Beta 3 Web patch: **38 changed/new files, 0 deletions**; reconstructs **805 / 805** final Web files exactly.
- ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations** across all release archives.
- SHA-256 checksum verification: **PASS**.
