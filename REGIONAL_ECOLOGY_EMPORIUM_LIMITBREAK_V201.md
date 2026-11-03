# Crystal Guild V2.0.1 — Regional Ecology, Moogle Emporium & Limit Break Relay

This source update extends V2.0.1 Encounter Rebalance without changing character levels, game schema, gear ownership, Relic claims, saved player regions, or item identifiers.

## Encounter ecology

- Reassigned bats and skeletons from Greenwind Plains to Whispering Caverns, levels 10 and 11.
- Reassigned Sahagin, Killer Fish, and Zu from Whispering Caverns to Sable Coast, levels 20–22.
- Reassigned Magitek Drones from Sable Coast to Magitek Wastes at level 31.
- Aligned the Bestiary habitat entries with the current 11-region normal encounter data. Adjusted regional weights and kept dedicated Hunts, Raid bosses, and World Event elite spawns out of ordinary random encounters.

## Moogle Emporium regional stocks

- Allows vendor-flagged Ascendant (Lv.90) and Singularity (Lv.95) weapons and armor, with a strictly scoped exception to the general Legendary-item exclusion.
- Keeps Relic, Paragon, crafted-only and unsellable exclusives out of vendor rotations.
- Covers the Lv.10–11 and Lv.60–64 shop progression gaps using neighboring ordinary equipment tiers.
- Guarantees at least one eligible weapon, armor and accessory where candidates exist. Automatically repairs legacy cached rotations lacking mandatory gear. The full eligible consumable catalog remains purchasable without the old gear-slot cap.
- Both Twitch and authenticated Portal purchases share the same item eligibility and inventory rules.

## Limit Break fix

The `LIVE_EVENT_ACTION` worker previously rejected `kind="limit"` before reaching the engine, although the Portal UI sent that value. The allowlist now includes the existing `limit` action, preserving authoritative Job Level, gauge, live-stream, round/run, and participation checks. The engine exposes `queued_action_kind` for clear Portal feedback. A ready queued Limit Break resolves on its scheduled combat round, then consumes its gauge and records the action only when executed.

Applies to Stream Ventures, World Events and Raids. Existing single-player Venture, Expedition, Dungeon, and Twitch `!limit` paths are retained.

## Validation

- 558 real shop-rotation combinations for 18 Jobs across 11 region entry/middle/exit checkpoints: all contained a weapon and armor.
- 97 focused Bot tests passed; four new end-to-end Limit Break tests verified Raid/Venture/World Event execution and rejection before 100% charge.
- 37 of 38 broad selected Web source tests passed; the remaining historical navigation-order assertion concerns an older portal layout.
- Additional older Bot suite run: 153 of 158 passed. Five historical tests still assume a 16 KiB Adventure State, four dungeons, or pre-rebalance encounter locations. These were not altered for the new release.
- No live Twitch deployment or production frontend build has been completed in this isolated source environment.

See the separate downloadable audit for install instructions and QA caveats.
