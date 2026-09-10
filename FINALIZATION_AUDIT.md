# Finalization Audit — Crystal Guild v1.7.1 Resynthesis Alpha 2 Hotfix 5 — Full Rest & Combat Continuity

**Decision: PASS — full-character recovery and combat termination now follow one consistent rule set.**

Rest is character-wide: HP and both persistent MP/AP families become fully refreshed, with the selected Job resolving that full state at its own resource maximum. This prevents stale or zero inactive resources without introducing a Job-switch refill exploit.

Combat is outcome-driven: round count cannot create a defeat. Living fights persist through Rally/normal encounters, Solo Ventures, Expeditions, Dungeons, Hunts, and administrative encounter/Raid resolution until a KO, enemy defeat, or deliberate supported retreat/withdrawal occurs. Technical resolver watchdogs preserve rather than terminate active combat.

The paired Web removes obsolete Dungeon round-limit presentation and updates Guide/What's New copy. Existing UI Revert & Button Fit styling and schema-16/protocol-33 Favorites authority remain unchanged.

Source regression: **704/704 Bot**, **588/588 frontend**, **71/71 hosted Web/API**. No migration or player reset.

Release contract: runtime/frontend `1.7.1-resynthesis-a2h5`; local schema **16**; hosted sync **1**; Portal protocol **33**.
