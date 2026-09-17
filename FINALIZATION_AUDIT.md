# Crystal Guild v1.8.0 Alpha 2 — Merc Service Finalization Audit

**Decision: PASS.** Alpha 2 completes the planned Merc Service balance and UX stabilization pass.

## Verified changes
- Visual Hunt / Venture / Raid deployment board with open/assigned state and quick roster navigation.
- Exact mission-specific availability reasons returned by the Bot and rendered by the Portal.
- Filled job types remain selectable/inspectable; the Portal no longer auto-jumps to another open slot.
- Hunt Seal fee tuning: Aerith 5, Tifa 6, Zidane 5, Yuna 7, Balthier 9, Cloud 12.
- Hero signature effects, three-slot contract rules, Hunt Seal earning, Quartermaster/Relic costs, and mission-scoped consumption remain unchanged.

## Regression result
- Frontend: **645/645 PASS**
- Hosted Web/API: **78/78 PASS**
- Bot: **729/729 PASS**
- Frontend production build command could not run in this extracted source workspace because local Vite dependencies are not installed (`vite: not found`). Source/unit/regression validation is complete.

## Release contract
- Runtime/frontend: `1.8.0-merc-a2`
- Local schema: **17**
- Hosted sync: **1**
- Portal Action protocol: **34**
- New migration: **none**
- Player reset: **none**

# Hotfix 2 Finalization Audit — Contracted Hero State

**Decision: PASS.** Active Merc contracts now propagate a distinct contracted roster state through Bot → Portal, and the active Hero uses unavailable artwork until the contract is cancelled or consumed.

Full regressions: **638/638 frontend**, **78/78 hosted Web/API**, **726/726 Bot tests + 30 subtests**. No schema, sync, protocol, migration, or player-reset change.

# Crystal Guild v1.8 Merc Service Alpha 1 — Hunt Seal Currency Hotfix

Runtime: `1.8.0-merc-a2`

# Finalization Audit — Merc Service Alpha 1 Batch 4

**Decision: PASS — code-only player-facing Merc Service layer is ready for artwork integration.**

Batch 4 adds no gameplay rebalance and no new persistent migration. The Batch 2 Merc mechanics and Batch 3 Portal actions remain authoritative. This pass adds Player Guide coverage, Quick Help, visible v1.8 identity, Twitch help routing, and responsive/mobile presentation.

Full regressions pass at **631/631 frontend**, **78/78 hosted Web/API**, and **726/726 Bot tests + 30 subtests**. Merc artwork was integrated in Batch 5. This hotfix reuses the established Hunt Seal economy and removes the temporary Hunt Marks currency path.
