# Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 3 Manual Check

1. Start on an AP Job, spend some AP, then switch to an MP Job.
2. Change equipment and/or trigger a normal full refresh while on the MP Job.
3. Switch back to the AP Job and confirm the stored AP value was not replaced with zero.
4. Repeat the same direction MP → AP → MP.
5. Test a character whose inactive resource was already zeroed before Hotfix 3; after the one-time compatibility repair, first use of that family should initialize normally.
6. Deliberately deplete AP or MP to exactly zero after Hotfix 3 is active; switch away and back and confirm it remains zero (no swap-refill exploit).
7. Verify Portal resource bars match the Bot state after each switch.
8. Verify Hotfix 2 Job Quest reconciliation and Hotfix 1 encounter-variety behavior still work.
