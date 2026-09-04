# Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 2

Bot hotfix for **Job Quest Unlock Repair**. Runtime: `1.7.1-resynthesis-a2h2`; paired Web remains `1.7.1-resynthesis-a2`; local database schema **15**; hosted sync **1**; Portal Action protocol **32**; command prefix `!`.

Job-unlock quests now self-reconcile. If a player has already satisfied every requirement for an unclaimed Job Quest, opening Jobs in the Portal, using `!job`, `!jobinfo`, or `!quests` completes the quest exactly once, awards its Gil/title rewards exactly once, and immediately makes the associated Job available.

The Encounter Variety safeguards from Hotfix 1 remain fully intact. No database migration or player reset is required.
