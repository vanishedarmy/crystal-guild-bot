# Portal Actions — Crystal Guild v1.7.1 Resynthesis Alpha 2 Hotfix 2

Portal Action protocol remains **32**. No hosted Web action type changes are required. Existing `CHARACTER_STATE` requests now reconcile any ready unclaimed Job Quests on the authoritative Bot before returning the Jobs list, so the current Alpha 2 Web immediately sees the corrected unlock state.
