# Crystal Guild v1.8.0 Alpha 2 — Merc Service Balance & UX

## Deployment board and availability clarity

- Current Contracts is now a visual three-slot deployment board for Hunt, Venture, and Raid.
- Assigned slots show the contracted Hero artwork and signature; open slots use the matching mission scene.
- Each slot jumps directly to that mission's roster and retains mission-scoped cancellation.
- The Portal no longer forces selection away from a filled job type, so players can inspect why the selected roster is unavailable.
- Every Hero now exposes an exact mission-specific reason: Available, progression Locked, unsupported job, occupied job slot, or On Contract.

## Hunt Seal balance pass

- Aerith: **5 Hunt Seals**
- Tifa: **6 Hunt Seals**
- Zidane: **5 Hunt Seals**
- Yuna: **7 Hunt Seals**
- Balthier: **9 Hunt Seals**
- Cloud: **12 Hunt Seals**
- Signature effects are unchanged after review; Alpha 2 tunes pricing rather than arbitrarily changing Hero identity.
- Hunt rewards, Quartermaster costs, Relic costs, and the established Hunt Seal wallet are unchanged.

## Release contract

- Runtime/frontend: `1.8.0-merc-a2`
- Local DB schema: **17**
- Hosted sync schema: **1**
- Portal Action protocol: **34**
- Player reset: **none**
- New migration: **none**

# Crystal Guild v1.8.0 Alpha 1 — Merc Service — Hotfix 3

## Mission-scoped Merc contract slots

- Merc Service now supports **three simultaneous contracts maximum**: one Hunt, one Venture, and one Raid.
- A mission type can have only one Hero reserved at a time.
- A Hero already on any active contract cannot be hired for another mission until that contract is consumed or cancelled.
- The Portal roster is filtered by the selected mission type. Heroes that do not accept that assignment, Heroes already contracted, and Heroes blocked by progression show unavailable artwork/state.
- If the selected mission slot is already reserved, every non-contracted Hero is unavailable for that mission.
- If Hunt, Venture, and Raid are all reserved, the entire roster displays unavailable until at least one slot opens.
- Contract consumption is mission-scoped: starting a Hunt consumes only the Hunt contract, Venture consumes only Venture, and Raid consumes only Raid.
- Cancellation is mission-scoped and remains non-refundable.
- Existing Hotfix 2 single-slot databases are upgraded in place while keeping schema version **17**; any active contract is preserved in its original mission slot.

## Release contract

- Runtime/frontend: `1.8.0-merc-a1`
- Local DB schema: **17**
- Hosted sync schema: **1**
- Portal Action protocol: **34**
- Player reset: **none**
- Hunt Seal economy: unchanged

# Hotfix 2 — Contracted Hero roster state

- Hired Hero now shows **CONTRACTED** in the Merc roster and switches immediately to unavailable card artwork.
- Contracted Hero shows the reserved mission instead of hire controls.
- Other unlocked Heroes remain visible as available, with hiring disabled while the single contract slot is occupied.
- Contract cancellation or deployment restores normal availability automatically.
- Hunt Seals remain the only Merc contract currency.

# Crystal Guild v1.8.0 Alpha 1 — Merc Service — Batch 4

## Player Guide, Quick Help & responsive polish

Batch 4 completes the code-only player-facing Merc Service layer before artwork integration.

### Web / Portal
- Visible Web identity is now **v1.8.0 Alpha 1 — Merc Service** (`1.8.0-merc-a1`).
- Player Guide adds a dedicated **Hero Merc Service** chapter and navigation entry.
- Guide documents the existing Hunt Seal economy already awarded by Hunts; Merc Service does not add a second Hunt currency.
- Guide documents all six Heroes, real unlock requirements, Hunt Seal fees, eligible mission types, and signature assists.
- Merc Service page now includes contextual `?` Quick Help and an inline **How Merc Contracts Work** briefing.
- Mobile adds an in-page Current / Roster / How It Works navigator, one-column roster behavior, touch-safe controls, and overflow protection.
- What’s New now leads with the v1.8 Merc Service Alpha 1 summary.
- Raid overlay asset cache-bust follows the v1.8 asset revision.
- Merc artwork remains intentionally absent until Batch 5.

### Bot help
- `!guild mercs` and `!guild merc` explain the Portal-first Merc Service, Hunt Seals, contract consumption, and cancellation rules.
- No new Twitch gameplay command is introduced; hiring remains authoritative through the Adventurer Portal.

### Release contract
- Runtime/frontend: `1.8.0-merc-a1`
- Local DB schema: **17**
- Hosted sync schema: **1**
- Portal Action protocol: **34**
- Player reset: **none**
- New migration in Batch 4: **none**
