# Crystal Guild v1.1.16 — Arsenal Release Notes

Arsenal expands the early and mid-game combat toolbox while adding more reasons to use it. Every Job now develops a broader active kit, elemental and special-effect information is surfaced directly where players choose abilities, and the lower-level Hunt, World Boss, and crafting curves have been filled in.

## Abilities expansion

All **18 Jobs** now have **6 active Battle Abilities** for **108 total abilities**. Active techniques are learned across **JLv.1, 8, 15, 22, 30, and 40**, while the existing JLv.1/15/30 abilities remain at their established unlock points.

New techniques reinforce each Job's identity with Fire, Ice, Lightning, Wind, Water, Holy, and Dark attacks plus effects already supported by Crystal Guild: Poison, Slow, Stun, Blind, Weaken, Vulnerable, Protect, Haste, Regen, cleansing, healing, HP drain, MP/AP recovery, piercing, and critical focus. No new multi-target selection system is introduced; Arsenal remains designed around the current single-enemy combat model.

Job-level unlock messages now call out newly learned Battle Abilities alongside passive Job milestones.

## Ability information at a glance

The same active-ability catalog remains authoritative across gameplay and reference surfaces. Job detail pop-outs, the Player Guide, and the interactive Solo Venture ability picker now show relevant elemental/special-effect traits in addition to JLv unlock, MP/AP cost, target, and description.

## New starter Hunts

Four new C-rank marks create a smoother Hunt path before the existing Lv.10 content:

- **Chieftain's Challenge** — Lv.2, Goblin Chieftain
- **Alpha on the Prowl** — Lv.4, Dire Wolf Alpha
- **Sting Operation** — Lv.6, Queen Hornet
- **Bones to Pick** — Lv.8, Ossuary Knight

Each has its own rewards, elemental weakness, enemy behavior, first-clear reward, and first-clear Title. Hunt lists continue to display in ascending level order.

## New early World Bosses

Four lower-level World Bosses now lead into Bomb King:

- **Goblin King** — recommended Lv.6
- **Hornet Empress** — recommended Lv.10
- **Skeleton Warlord** — recommended Lv.14
- **Gigas Chief** — recommended Lv.18

Each includes its own HP/reward curve, phases, signature attack, drops, enrage timing, and raid attack cadence.

## New low-level crafting

Eight practical consumable recipes have been added for Lv.3–15 adventurers:

- Field Hi-Potion
- Antidote Satchel
- Echo Herb Bundle
- Stamina Draught Mix
- Ether Distillation
- Iron Tonic Mix
- Smoke Bomb Kit
- Remedy Kit

These recipes use existing low-level consumables and common monster materials and are intended to make early drops useful before higher-tier forge/crafting progression opens up.

## What's New

The Adventurer Portal's reusable **What's New** section now features Arsenal and points players directly to the Jobs tab to explore the expanded ability catalog. Wayfarer remains available under previous major updates.

## Compatibility

- Runtime: `1.1.16-arsenal`
- Frontend asset revision: `1.1.16-arsenal1`
- Local DB schema: **5** (unchanged)
- Hosted sync schema: **1** (unchanged)
- Hosted sync compatibility: `1.1.15-wayfarer` (unchanged)
- Portal Action protocol: **14** (unchanged)
- Twitch command prefix: `!`

Arsenal requires matching **Bot + Web** files because gameplay data and the player-facing catalogs both change. It does **not** require a database migration, player reset, new Render secret, or new Twitch OAuth scope.
