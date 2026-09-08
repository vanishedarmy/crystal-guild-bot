# Finalization Audit — Crystal Guild v1.7.1 Resynthesis Alpha 2 Hotfix 5

**Decision: PASS — Treasure Seekers Solo Progress.**

The missing link was isolated to the Solo treasure branch: it incremented `solo_venture_treasures` but did not call Fellowship `record_activity(..., "treasure")`. The branch now records one stage-scoped `treasure` event at chest discovery, using `solo_treasure:<player>:<run>:<stage>` for idempotency.

This advances weekly **Treasure Seekers**, the long-term **Treasure Hunters** deed, and any future Fellowship consumer of the same canonical `treasure` activity. Stream/Rally treasure handling remains compatible, while the current Hotfix 5 Rally rule stays **100% Encounter / 0% Treasure Chest** and Solo stays **80% / 20%**.

Bot runtime `1.7.1-resynthesis-a2h5`; paired Web `1.7.1-resynthesis-a2h5`; schema **15**; hosted sync **1**; Portal protocol **32**; prefix `!`. No database migration or player reset.
