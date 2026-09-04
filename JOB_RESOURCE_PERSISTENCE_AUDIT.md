# Job Resource Persistence Audit — v1.7.1 Resynthesis Alpha 2 Hotfix 3

## Reported symptom
Switching between Jobs that use different active-resource families could show the destination MP/AP meter at **0**. Switching back to the previous resource family restored its previous value.

## Root cause
The Job switch itself was not resetting resources. Two shared normalization paths were overwriting the **inactive** resource family:

1. `_full_refresh_player_row()` wrote both `current_mp` and `current_ap` on stream-live/Long Rest refresh. An MP-only Job therefore wrote AP as `0`; an AP-only Job wrote MP as `0`.
2. `_normalize_after_equipment_change()` clamped both resource columns to the active Job's maximums. Because the inactive family's maximum is zero, any stored inactive value could be replaced by `0` after an equipment change.

The later Job switch then loaded that persisted zero correctly, which produced the visible bug.

## Hotfix 3 correction
- Full player refreshes restore HP plus only the MP/AP family actually used by the current Job.
- Equipment normalization clamps HP plus only the current Job's applicable MP/AP family.
- The inactive resource column is left untouched in both paths.
- Existing `_resource_state_for()` semantics remain unchanged: MP/AP persist as absolute resource-family values across battles and Job changes, and `NULL` means that family has never been initialized.

## Existing-player compatibility repair
Older builds may already have destroyed an inactive value by storing `0`. Because the database has no historical flag that distinguishes a synthetic inactive zero from a genuinely depleted inactive pool, Hotfix 3 performs one bounded compatibility repair on startup:

- only a resource family that is **inactive for the player's current Job** is eligible;
- only an exact stored value of `0` is changed;
- the value becomes `NULL`/uninitialized, so the next Job that genuinely uses that family initializes normally;
- nonzero inactive values are never changed;
- dual-resource Jobs are never altered;
- a runtime-state receipt (`resource_pool_switch_h3_repair`) prevents the repair from running more than once.

The one-time nature is important: after the receipt exists, a legitimately depleted `0` resource remains `0` through Job switching and cannot be refilled by swapping Jobs.

## Verification
Focused Hotfix 3 coverage confirms:

1. an inactive resource survives both full refresh and equipment normalization unchanged;
2. a legacy inactive zero is repaired once and initializes normally when its resource family is next used;
3. a legitimate post-repair zero remains zero after switching away and back, preventing a Job-swap refill exploit.

Full Bot regression: **686 / 686 PASS**. Unchanged paired Web compatibility: **562 / 562 frontend PASS** and **65 / 65 hosted Web/API PASS**.

## Contract
Bot runtime `1.7.1-resynthesis-a2h3`; paired Web `1.7.1-resynthesis-a2`; local schema **15**; hosted sync **1**; Portal Action protocol **32**. No database migration or player reset is required.
