# Crystal Guild v1.9.97.6 — Job-Level Reward Balance

## Changes
- Active Job Level alone determines the level-difference multiplier applied to Job Points (JP). Removed the old 35%-of-character-level JP catch-up floor. The bounded existing 0.05×–1.5× modifier still applies; base enemy JP remains unchanged.
- Character XP and Gil remain tied to character-level difficulty. This prevents high-level characters from exploiting trivial enemies for character levels or currency while allowing sensible progression on newly switched Jobs.
- The separate repeat Dungeon completion JP multiplier now uses active Job Level. First-clear XP/JP/Gil and crafting materials retain their previous treatment.
- Existing Solo Ventures, Expeditions, standard battles, World Events and Dungeon encounter JP calculations now use that same corrected helper; fixed Hunt rewards remain independent of character-level modifiers.
- No stat, ability, class mastery, item, or saved progression migration is required.

## Limitations
- Raid victories currently grant character XP and Gil, not Job Points. This release does not add raid JP; that is a distinct reward-design decision.
- Enemy selection and entry eligibility remain based on existing character/region gates for safety. Only Job Point reward scaling changes.
- No changes to underlying JP-to-next-level formula or existing earned rewards.
