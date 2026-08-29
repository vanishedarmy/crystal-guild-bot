# Crystal Guild v1.3.1 — Asset Optimization Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **486 / 486 PASS**.
- Frontend Node regression suite: **361 / 361 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

The Bot suite still includes intentional simulated acknowledgement loss, Twitch/live-status outages, corrupt checkpoint recovery, restart recovery, database recovery drills, and synthetic stress scenarios. Those warning/error log lines are expected fixtures.

## Source validation
- Python source compilation: **90 / 90 PASS** across Bot + Web source trees.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **185 / 185 PASS**.
- Plain JS/MJS `node --check`: **147 / 147 PASS**.
- Literal WebP route audit: **222 routes checked / 0 missing**; dynamic artwork routes remain covered by the full frontend regression suite.

## Asset optimization
- Remaining shipped PNG artwork audited: **390**.
- Accepted PNG → lossless WebP conversions: **390 / 390** because every converted file was smaller.
- Exact decoded RGBA comparison: **390 / 390 PASS**, including alpha/transparency.
- Converted PNG bytes: **151,212,726**.
- Replacement WebP bytes: **117,726,632**.
- Conversion savings: **33,486,094 bytes (31.93 MiB)**.
- Entire public asset tree: **192,075,128 → 158,588,698 bytes**, a reduction of **31.94 MiB (17.4%)**.
- Public artwork state: **0 PNG / 572 WebP**.
- Existing 182 WebP assets were separately tested for lossless repacking; only ~0.6 KiB of safe savings was available, so they were retained to avoid pointless churn.
- Public `guide-data.json` was compacted without content loss.

## Compatibility / continuity
- Runtime/frontend identity: `1.3.1-asset-optimization`.
- Local DB schema: **9** unchanged.
- Hosted sync schema: **1** unchanged.
- Portal Action protocol: **22** unchanged.
- Twitch prefix: `!`.
- Database migration: **none**.
- Player reset: **none**.
- OAuth change: **none**.
- New environment variables: **none**.
- Gameplay/economy/balance changes: **none**.
- v1.3 Guild Expansion shared-state, Airship, Fellowship, Expedition, inventory, recovery, and persistence regressions remain green.

## Patch/package verification
- v1.3.0 → v1.3.1 Bot patch: **14 changed/current files, 0 deletions**.
- v1.3.0 → v1.3.1 Web patch: **457 changed/new files, 390 obsolete PNG deletions**.
- Patch reconstruction: exact final Bot and Web trees.
- ZIP CRC/integrity: all release archives PASS.
- Runtime/private-artifact hygiene: 0 violations.
- SHA-256 verification: PASS.
