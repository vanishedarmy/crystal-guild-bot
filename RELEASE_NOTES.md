# Crystal Guild v1.1.19 — Retro Phase III / Release Candidate 1

RC1 is the finalization checkpoint for Retro Phase III before v1.2 Expeditions. It consolidates the current gameplay/data state, performs a release-wide balance and integrity audit, and pairs with the final RC Web presentation pass.

## Gameplay and progression state
- Chocobo portrait selection remains authoritative and persistent.
- Facility Supply Balance remains intact: all six Fellowship facility materials have multiple monster sources and practical early-game access.
- No new gameplay mechanics are introduced in RC1.
- No progression reset is required.

## Finalization audit
RC1 statically validates:
- every monster drop references a real item and uses a valid probability;
- every region encounter references a real monster;
- each region retains multiple encounters within its minimum-level +10 safety band;
- every facility material has at least three monster sources, an early source at Lv.11 or below, and an early practical drop rate;
- shop availability remains populated throughout Lv.1–50.

See `FINALIZATION_AUDIT.md` for the full result.

## Cleanup
- Removed superseded Arsenal II / Hotfix / Passive Recovery staging documents from the shipping Bot root.
- Removed Python bytecode and cache directories from the release tree.
- Preserved only current setup, recovery, combat, deployment, and release documentation.

## Compatibility
- Bot runtime: `1.1.19-retro-phase-iii-rc1`
- Local DB schema: **6** unchanged from Chocobo Portraits
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **15** unchanged
- Twitch command prefix: `!`
- Player reset: **none**
- OAuth change: **none**
- New environment variables: **none**
