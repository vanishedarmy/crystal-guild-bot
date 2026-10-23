# Crystal Guild v1.9.8 — Consumable Effects Audit Hotfix

Scope: Bot-side authoritative item use, recovery preview, and regression coverage. No schema change, no Web bundle changes, no item price or base damage rebalance.

## Megalixir behavior

- In Active Battle and Raid / World Event battles, a Megalixir **fully restores the current HP and applicable MP/AP of every living ally at the moment the item resolves**. It **does not revive** KO'd heroes.
- Items act **before** enemy attacks in the same combat round. The enemy response and status damage can lower HP again before the final round-end overlay / Portal snapshot. This timing is intentional; using the item does not make the party invulnerable for the rest of the round.
- Battle-use logs now explicitly label full HP restoration **"FULL HP at item resolution"** and full MP/AP restoration **"FULL MP" / "FULL AP"**, distinguishing a successful heal from damage that followed later in the round.
- Elixir and Tent retain their previous targeting restrictions (Elixir: one conscious ally, Tent: field use) and their full HP/MP/AP recovery effects.

## Corrections and verification

- One shared capped-recovery rule is now used by field use, standard battle, Raid/World Event battle, and field inventory previews.
- 100% fraction effects **set the applicable resource directly to maximum**. Partial fraction effects restore at least one point when the target has a positive resource pool, avoiding integer truncation to zero for tiny MP/AP pools.
- Fixed HP restore amounts are unchanged: Potion 50, Hi-Potion 200, Mega-Potion 500, X-Potion 1,000, all capped by missing HP.
- Percentage MP/AP restoratives are unchanged at 40% / 65% / full, subject to the minimum-one rule and resource cap.
- Damage item base values are unchanged: Bomb Fragment 220 Fire, Arctic Wind 300 Ice, Lightning Marble 300 Lightning, Water Gem 450 Water, Earth Drum 450 Earth, Shadow Gem 700 Dark. Standard Active Battle retains its +30% matching-weakness rule; Raid bosses currently have no item-element weakness rules.
- Status cures, stat buffs and Phoenix Down continue using existing item catalog effects. No item is consumed if it has no effective resolution.
- Updated the stale historical catalog-count test from 437 to the current 440 entries (the three Airship materials were already in v1.9.8). No new item, inventory balance reset, database migration, or Portal/frontend rebuild is required.

## Install

Extract the Bot patch over the **existing v1.9.8 Bot directory** from the *Stream & Portal Repair* hotfix, retaining any live `.env`, database, logs, private tokens and `overlay/state.json`. Alternatively use the complete sanitized Bot source archive in a staging folder and migrate only source files into the deployment. Restart the Bot. The matching Web from the Stream & Portal Repair hotfix stays unchanged.

## Validation boundaries

Automated tests exercise catalog full-restore contracts, field consumables, mixed-party standard battle and Raid resolution, listed offensive consumables, weakness bonus, caps, and inventory consumption. Real Twitch chat, live Raid boss response, actual Web overlay, and production database were not accessed. A final round-end HP value below full after Megalixir can still be correct if the combat log shows subsequent incoming damage.
