# Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 5

## Gear Favorites Authority Fix

Gear Favorites are now part of the authoritative Crystal Guild player state instead of relying on a hosted/browser preference copy.

- New local table `player_gear_favorites` stores each player's equipment Favorites.
- New Portal action `SET_GEAR_FAVORITES` writes the complete favorite set to the Bot database using replay-safe action receipts.
- Player inventory snapshots carry the owner's private `favorite_item_ids` to the hosted Portal; public inventory endpoints strip that private preference field.
- Desktop, mobile, and other signed-in browsers read the same synced player-state list.
- The prior hosted-only preference row remains only as a temporary migration/pending mirror while a Bot write is in flight.
- Existing browser-local and prior hosted-only Favorites are preserved as migration sources and promoted into the authoritative player profile.
- Empty Favorites are authoritative too, so clearing the final star on one device propagates correctly.
- Returning to an open Equipment tab rechecks synced Favorites; rapid taps use last-write-wins behavior without stale-state loss.

## Compatibility

Treasure Seekers Solo progress, Rally 100% Encounter / 0% Treasure, Solo 80% / 20%, Weapon + Armor Best use, mobile Guide/Retainer cleanup, ☆/★ controls, level-descending gear, and removal of `Replaces X` remain intact.

Runtime/frontend remains `1.7.1-resynthesis-a2h5`. Local schema advances to **16**, hosted sync remains **1**, and Portal Action protocol advances to **33**. The migration is automatic and creates a verified pre-schema-16 backup. No player reset.
