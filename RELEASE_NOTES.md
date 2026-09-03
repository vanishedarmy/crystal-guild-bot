# Crystal Guild v1.7.1 — Resynthesis Alpha 1

Resynthesis adds a third Guild Blacksmith service for permanently breaking down unwanted **weapons and armor** into useful crafting materials. The service is available through the Adventurer Portal and `!resynthesize <gear>`.

## Alpha 1 scope

- Weapons and armor can be resynthesized; accessories are excluded.
- Relic, Artifact, unique/protected, and otherwise unsellable equipment cannot be resynthesized.
- The last equipped copy must be unequipped before it can be destroyed.
- Recovery is deterministic and displayed before confirmation.
- Base recovery is deliberately worth less in immediate resale Gil than selling the original equipment, preserving **Sell → Gil** and **Resynthesize → materials** as distinct choices.
- Forged equipment receives a modest material bonus only when the final owned copy is destroyed. This matches the current per-player/per-item forge-level model and prevents duplicate-copy forge-refund loops.
- Final-copy resynthesis clears that item's forge-level row so reacquired gear begins at +0.
- Rift Crystal, Dark Matter, Relic materials, and Artifact materials are not refunded through forge bonuses.

## Release contract

- Runtime/frontend: `1.7.1-resynthesis-a1`
- Local DB schema: **15**
- Hosted sync: **1**
- Portal Action protocol: **32**
- Twitch prefix: `!`
- Baseline: **v1.7.0 — Moogle Retainer UI Hotfix 3**

There is no database migration or player reset. Existing Guild, Retainer, Gold Saucer, Blacksmith, inventory, forge, and progression state carries forward.
