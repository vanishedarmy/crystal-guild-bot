# Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 5 — Full Rest & Combat Continuity

This correction fixes two core combat-state rules.

## Full-character Rest

Camp completion, Long Rest, Tent, stream-start recovery, and full-recovery administration now restore the character as a whole. HP is restored to maximum and both persistent Job-resource families are marked fully refreshed. Because MP/AP maxima can differ between Jobs, the database stores an explicit full-resource state rather than one Job's concrete number. Selecting any MP- or AP-based Job after the Rest therefore resolves that family at that Job's own maximum. Ordinary Job switching does not refill a legitimately depleted resource.

## Combat continuity

Round count is telemetry, not a defeat condition. Rally/normal encounters, Solo Ventures, Expeditions, Dungeons, Hunts, and admin-assisted encounter/Raid resolution no longer manufacture a loss after a fixed number of rounds. Combat ends only when the enemy is defeated, the hero/participating party is KO'd, or a supported retreat/withdrawal is deliberately initiated. Technical auto-resolution watchdogs may pause an automated resolver, but preserve the living battle instead of converting it into defeat.

Dungeon pressure encounters retain opening statuses/resource strain, but their former round-count loss mechanics and UI denominator are removed. Player Guide/What's New copy now documents the same rule.

## Compatibility

The UI Revert & Button Fit presentation remains intact. Authoritative cross-device Gear Favorites remain under schema **16** / Portal protocol **33**. Treasure Seekers Solo progress, Rally 100% Encounter / 0% Treasure, Solo 80% / 20%, Weapon + Armor Best use, mobile Guide/Retainer cleanup, ☆/★ controls, level-descending gear, and removal of `Replaces X` remain intact.

Runtime/frontend remains `1.7.1-resynthesis-a2h5`; hosted sync remains **1**. This correction requires no database migration and no player reset.
