# Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 3

## Job Resource Persistence

Hotfix 3 fixes MP/AP meters dropping to zero after switching between Jobs that use different resource families.

### Root cause
Older refresh and equipment-normalization paths wrote the inactive resource family as zero. For example, refreshing while an MP-only Job was active could overwrite the player's stored AP with `0`; switching to an AP Job then correctly loaded that corrupted zero, while switching back restored the untouched MP value.

### Fix
- Stream-live and Long Rest refreshes restore the **active Job's** HP/resource pool without overwriting the inactive MP/AP family.
- Equipment changes clamp only the active Job's applicable resource pool and preserve the inactive family unchanged.
- MP and AP therefore continue to persist independently across Job changes.
- Legitimately depleted pools remain depleted; switching Jobs is not a resource-refill mechanic.

### Existing-player compatibility
A one-time startup repair checks existing players for an inactive MP/AP value of zero that may have been written by the old bug. Those inactive zeros are returned to `NULL`/uninitialized once, allowing the next Job that actually uses that resource family to initialize normally. A runtime-state receipt prevents the repair from running again, so it cannot be exploited for repeat refills.

Hotfix 2 Job Quest reconciliation and Hotfix 1 Encounter Variety remain carried forward unchanged.

Bot runtime advances to `1.7.1-resynthesis-a2h3`. Paired Web remains `1.7.1-resynthesis-a2`. Local schema **15**, hosted sync **1**, Portal protocol **32**, prefix `!`. No database migration or player reset.
