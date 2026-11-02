# Crystal Guild v1.9.97.7 — Bot Integration V2.9

## Baseline
Extends **V2.8 integrated Python Bot**, not the original unmodified Bot. Existing 618 items and 108 Relic configurations are unchanged. No production Bot or Web files have been modified.

## Implemented in the authoritative Python Bot

### Thief — Mug / Master Pickpocket
- The existing `mug` battle ability now attempts to steal from the **actual encounter monster's drop table**, in both active encounters and raids, only after a damaging Mug strike spends its combat cost.
- One attempt per player per unique encounter (failed attempts also consume the opportunity). Base success chance: **10%**, plus the verified equipped Thief Relic's Master Pickpocket trait value; capped at **35%**.
- Loot is restricted to exactly **one** common/uncommon/rare material or consumable. No Relic, Unique, Exotic, equipment or quest reward may be stolen. No target with no eligible loot can produce an item.
- Database schema **28** adds `relic_steal_attempts`, whose unique encounter/player key prevents replay or repeated worker rewards. Inventory, transaction and receipt are committed in the **same SQLite transaction**. A failed write rolls them all back.
- Stealing grants loot immediately after a successful paid Mug, independent of winning or losing the battle. The once-per-encounter limit applies to both outcomes.

### Blue Mage — Enemy Technique Memory / Mimic Insight
- The existing enemy special-action resolver supports genuine, **observed** spell mastery (not arbitrary player-reported spells) for these exact matches:
  - Chimera/Sea Serpent/Blue Dragon etc. `aqua_breath` -> Aqua Breath
  - Malboro variants `bad_breath` -> Bad Breath
  - Cactuar `1000_needles` -> Thousand Needles
  - Enemy `mighty_guard` -> Mighty Guard, where that action exists
- A living Blue Mage who meets the spell's job-level requirement rolls **25% + equipped Relic Mimic Insight** (capped at 50%) once per spell per fight when the enemy actually casts it.
- Table `blue_magic_memories` stores mastered techniques permanently and without duplicates. Mastering a matching *damaging* spell increases its damage by **5%**, in addition to existing Ultimate Relic Adaptive Memory, only when using that spell.
- Job-level ability unlocks are **not removed or gated**: this is a compatible mastery progression, not a replacement learn-to-cast system.
- This observing hook is connected to **active enemy special actions** (ventures/hunts/world events using that resolver). Boss scripted raid mechanics are not yet hooked into this observation path.

## Still pending
- Beastmaster's persistent tame/owned-pet roster, permissions and per-pet combat actions. The current Call Beast / King of Beasts are non-owned attacks; no ownership data is invented.
- Additional Blue Magic source-to-spell pairings and scripted raid boss skills, plus Web/Player Guide sync.
- Full Twitch deployment, real shared DB end-to-end QA, and full project-wide suite.

## Validation
- New V2.9 tests: **19/19** passed.
- Focused integration regression including new tests: **104/104** passed.
- SQLite migration verified from schema 27 to 28: retains player data, creates both new tables, and generates a pre-migration backup.
- Python compileall, archive CRC validation and source integrity checks passed.

## Installation
For an existing V2.8 installation use the V2.9 **merge patch**; for a clean replacement source use the **complete Bot ZIP**. Never apply both. Back up the Bot directory and database, test in a sandbox, and only then consider deployment. No Web modifications in this checkpoint.
