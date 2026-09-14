# Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 5 — Personalized Chat Results + Raid XP Boost

This focused Bot + Web update improves Twitch settlement readability and raises Raid progression rewards without changing combat rules, schemas, or Portal action semantics.

## Personalized Venture and Raid results
- A finished Rally Venture or Raid posts one concise encounter-wide result first.
- Every participating viewer then receives a separate Twitch chat line beginning with their `@username`.
- Venture personal results include damage dealt, damage taken, healing, standing/KO state, XP, JP, Gil, loot, and notable level/achievement notices when present.
- Raid personal results include damage, healing, mitigation, damage taken, standing/KO state, personal XP/Gil allocation, and personal item drops.
- Raid wipes and Venture defeats still give each participant a personal contribution line even when there are no victory spoils.
- Personal result lines are deliberately not packed together by the Twitch sender and are paced at 1.5 seconds to improve readability and avoid a sudden result burst.
- Aggregate participant reward/loot walls are removed from the final summary; special Fellowship notices remain separate when they occur.

## Raid XP +50%
- Configured Victory XP for all 37 Raid/Trial bosses is increased by exactly 50%.
- The existing bounded Raid allocation formula is unchanged: the larger XP pool is still shared using both participation and contribution.
- Gil, item drop chances, contribution weighting, mechanics, HP, timers, and settlement safety are unchanged.
- Portal boss data, contextual Raid help, and the Player Guide show/explain the updated XP values.

## Compatibility
Runtime/frontend `1.7.1-resynthesis-a2h5`; local schema **16**; hosted sync **1**; Portal protocol **33**. No database migration or player reset. HTTP Response Efficiency, Contextual Quick Help, Battle Item Purpose Sort, control-fit work, Full Rest & Combat Continuity, and authoritative Gear Favorites remain intact.
