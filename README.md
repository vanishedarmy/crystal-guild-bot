# Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 3

Bot hotfix for **Job Resource Persistence**. Runtime: `1.7.1-resynthesis-a2h3`; paired Web remains `1.7.1-resynthesis-a2`; local database schema **15**; hosted sync **1**; Portal Action protocol **32**; command prefix `!`.

Hotfix 3 fixes MP/AP state being erased when a player changed to a Job that uses the other resource family. Stream/Long Rest refreshes and equipment normalization now restore or clamp only the resource family used by the active Job and leave the inactive family untouched.

A one-time startup compatibility repair converts inactive zero values that older builds could have written back to an uninitialized state. That repair is receipt-protected and cannot be repeated to refill resources by Job swapping. Legitimately depleted resource pools continue to persist at zero after the repair has run.

Job Quest unlock repair from Hotfix 2, Encounter Variety from Hotfix 1, Resynthesis, and the Alpha 2 Gold Saucer rebalance remain intact. No database migration or player reset is required.
