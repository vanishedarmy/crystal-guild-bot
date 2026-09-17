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
