# Crystal Guild v1.4.0 — Dungeons & Delves Alpha 3 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **510 / 510 PASS**.
- Frontend Node regression suite: **381 / 381 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

The Bot suite includes intentional simulated acknowledgement loss, Twitch/live-status outages, corrupt checkpoint recovery, and restart/recovery fixtures; their warning/error log lines are expected.

## Alpha 3 Dungeon coverage
- GameData validation: **3 Dungeons / 0 errors**.
- The Whiteglass Bastion unlocks at Lv.26 + 45% Frostveil Reach and exposes 9 chambers / 2 Crossroads.
- Forward route modifiers persist in active run state, survive save/load, apply to the correct later hazard/combat, and are consumed once used.
- First-clear bonuses settle once per Dungeon using existing progress records.
- Existing run/chamber stale-tab binding and replay protection remain green.
- Adventure Board with all three Dungeons unlocked serializes to **15,449 bytes**, leaving **935 bytes** below the 16 KiB guardrail.

## Source / asset validation
- Python compile sweep: **93 / 93 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **192 / 192 PASS**.
- Plain JS/MJS `node --check`: **152 / 152 PASS**.
- Literal image-route audit: **159 routes / 0 missing**.
- Public artwork: **0 PNG / 576 WebP**.

## Compatibility
- Bot/Web/frontend runtime: `1.4.0-dungeons-a3`.
- Local DB schema: **10** unchanged from Alpha 2.
- Hosted sync schema: **1** unchanged.
- Portal Action protocol: **24** unchanged.
- Twitch prefix: `!`.
- Database migration: **none from Alpha 2**.
- Player reset: **none**.
- OAuth/environment changes: **none**.
- Non-Dungeon gameplay/economy rebalance: **none**.

## Patch/package verification
- Alpha 2 → Alpha 3 Bot patch: **23 changed/new files, 0 deletions**; reconstructs **150 / 150** shipping Bot files exactly.
- Alpha 2 H1 → Alpha 3 Web patch: **53 changed/new files, 1 stale patch-manifest deletion**; reconstructs **820 / 820** shipping Web files exactly.
- The Alpha 3 Bot package restores the canonical `crystal_guild/token_store.py` source module omitted by the Alpha 2 Bot archive; no token data/secrets are packaged.
- Six release ZIPs: CRC/integrity **PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **PASS**.
