# v1.9.97.2 — Live World Events & Progression Balance

- Dungeon and Ascension encounters no longer reuse World Event boss source templates; three Elite boss templates are removed from offline expedition/region spawns. Ordinary species remain available in regional exploration.
- The stream-status daemon withdraws active World Events when the stream ends. If the source stream ends during the fight, no World Event victory is awarded. Live status is polled on the existing 30-second cadence.
- Elite World Events gate entry individually at level 80/85/95. Regular World Events retain their normal accessibility.
- Overleveled monster XP, JP and Gil sharply diminish with player-enemy level difference (floor 5%), favoring near-level battles. Existing character XP, JP, level thresholds, and stat curves are not retroactively changed.
- Repeat Dungeon completion XP/JP/Gil scales with player-to-dungeon level difference; first-clear bonuses, titles, and item rewards are preserved.
- Normal monsters do not inherit any event-only 4x XP, 3x JP, or 2x Gil multipliers.
- The existing Dungeon, Ascension, World Event, and Bestiary catalog data are updated and validated. Existing player rewards/progress are not deleted.

**Limitations:** This is the first progression-balance pass, not a complete rework of every Job, ability, boss, and equipment curve. Staging validation with live Twitch and the Portal is required.
