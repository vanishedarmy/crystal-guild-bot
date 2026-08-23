# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 3

Hotfix 3 is a focused combat/UI correction on the Cloud Continuity Hotfix 2 baseline. It preserves the randomized Daily Guild Provisions and Twitch subscriber-tier work from Hotfix 2.

## Raid round actions restored

Raid participants can now queue the same core combat choices used by Active Battles:

- `!attack`
- `!ability <name> [target]`
- `!defend`
- `!use <item> [target]`

Each living raider gets one action per Raid round. A newer choice replaces that hero's earlier queued choice until the round resolves. A hero who submits no action still defaults to Attack so Raid timers cannot stall.

Raid abilities now use their normal MP/AP costs and supported effects, including damage, healing, resource restoration, revive/cleanse, and combat statuses. Raid item use consumes the item only when its queued effect successfully resolves. Defend is a real Raid action: it restores the normal defensive MP/AP amount and reduces incoming boss damage for that round. Winning-round HP and MP/AP state is persisted before the Raid runtime is cleared.

Recovered pre-Hotfix-3 Raid checkpoints are hydrated into the new queue state when first touched, so an already-active Raid can continue without a schema migration.

## Rally Venture presentation cleanup

The Adventurer Portal no longer renders a live stream Venture as a separate Active Battle card below Current Region. An active `kind=venture` encounter is rendered inside the existing **Rally Venture** panel, keeping the Adventure Board hierarchy together.

Hunts and legacy non-Rally Active Battle states retain their appropriate standalone presentation.

## Selectable-control readability pass

Interactive controls received a clarity pass across the Portal:

- stronger text/background contrast and selected-state treatment;
- visible keyboard focus treatment and preserved touch targets;
- readable disabled controls without making labels disappear;
- clearer action labels that name their target, such as `Travel to <region>`, `Equip <item>`, `Use <item>`, `Craft <item>`, `Forge <item>`, `Buy <item>`, and `Sell <item>`;
- clearer Hunt filters and Job/stance selection labels.

The Player Guide now explicitly documents Raid round actions and their default-Attack behavior.

## Compatibility

- Bot runtime: `1.1.14-cloud-continuity-h3`
- Hosted sync version/snapshots: `1.1.14-cloud-continuity`
- Matching Web asset revision: `1.1.14-continuity3`
- Local DB schema: 4
- Hosted sync schema: 1
- Portal Action protocol: 12
- Twitch prefix: `!`
- Database migration: none
- Player reset: none
- New Render secrets: none
- New OAuth scope: none

Hotfix 2's subscriber feature still requires `channel:read:subscriptions` on the broadcaster token if that authorization has not already been completed. Hotfix 3 itself introduces no additional Twitch authorization requirement.
