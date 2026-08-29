# Crystal Guild v1.3.0 — Guild Expansion Beta 3

## Shared-State Hardening & Stability

Beta 3 keeps the v1.3 feature set and Beta 1 balance frozen while hardening the shared Fellowship/Airship mutation paths used by multiple players, browser tabs, reconnects, and the streamer controls.

### Fellowship contribution safety
- Guild contributions now recompute the live remaining requirement while holding the authoritative Guild write lock. Simultaneous contributors cannot overfill a requirement or lose more Gil/materials than the project still needs.
- The final contribution, contribution Renown, project completion, facility/Airship upgrade, shared reward, Fellowship level synchronization, Orders/Deeds, and Legacy settlement complete beneath one outer transaction.
- Active-project selection is validated and changed under the same serialized Guild lock, preventing a project switch from splitting a just-completed requirement from its upgrade/reward.
- Portal contribution actions now carry the `project_id` that was visible in the player's Fellowship tab. If the streamer changed projects before the action arrives, the contribution fails closed and returns refreshed Fellowship state instead of donating to the wrong project.

### Multi-tab / replay safety
- Fellowship Portal mutations re-check the bounded Portal replay receipt after obtaining the write lock. Two tabs/retries that arrive before the first acknowledgement commits can no longer both execute the same mutation.
- Existing replay-safe Workshop actions inherit the same stronger locked re-check.

### Airship hardening
- Airship mission launch is serialized and conditionally starts only while no other run is active. Concurrent streamer launch requests cannot overwrite one another.
- Due mission settlement re-reads the active run inside the write transaction and scopes cleanup to that exact run ID.
- Guild Renown, contributor Gil/personal Renown, mission history, completion counters, and replay receipts settle together.
- Restart/reconnect settlement remains automatic and cannot duplicate contributor rewards or clear a newer mission.

### Player-facing behavior
- What's New explains the reliability changes without exposing internal database/transaction terminology.
- The Beta 2 Fellowship priority layout, remembered disclosures, Founding Hall portrait art, collapsible Equipment inventory groups, Beta 1 economy tuning, Alpha 3 services, Airship formulas, Weekly Order payouts, and Guild Legacy targets are unchanged.

### Compatibility
- Bot runtime: `1.3.0-guild-expansion-b3`
- Hosted Web runtime: `1.3.0-guild-expansion-b3`
- Frontend asset revision: `1.3.0-guild-expansion-b3`
- Local DB schema: **9** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **22** (advanced from 21 for project-bound Fellowship contributions)
- Twitch prefix: `!`
- Player reset: **none**
- New environment variables: **none**
- OAuth changes: **none**

Because the Portal Action protocol advances, deploy the Beta 3 Web and Bot together.
