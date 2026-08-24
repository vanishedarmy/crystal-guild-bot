# Crystal Guild v1.1.16 — Arsenal Hotfix 6 Release Notes

Arsenal Hotfix 6 tightens the randomized Daily Guild Provisions reward pool.

## Daily provisions

Daily provisions now use an explicit opt-in catalog of ordinary reward items instead of selecting any item that happens to match a broad type, rarity, and value rule.

This means:

- **Chocobo Registration Writs can never be rolled from Daily Guild Provisions.**
- Other special/progression items are excluded by default.
- Ordinary level-appropriate shop consumables remain eligible.
- Approved common/uncommon crafting materials remain eligible.
- New future items must be deliberately added to the Daily provisions catalog before they can appear.
- Subscriber Tier 1/2/3 bonus roll counts and Gil bonuses are unchanged.
- The 24-hour Daily cooldown is unchanged.

The Chocobo Registration Writ remains obtainable only through its intended Chocobo Stable progression/purchase path.

### Existing orphaned Writ repair

A Writ previously granted by the old Daily pool could exist in inventory without the authoritative `player_chocobos` purchase/timer record. That invalid state could block a later legitimate Writ purchase. Hotfix 6 detects this specific orphaned state and removes only the invalid inventory Writ, recording the cleanup in the transaction ledger. Legitimately purchased/timed Writs always have the authoritative row and are left untouched.

## Compatibility

- Bot runtime: `1.1.16-arsenal-h6`
- Hosted Web runtime: `1.1.16-arsenal-h5` unchanged
- Frontend asset revision: `1.1.16-arsenal1h5` unchanged
- Local DB schema: 5 unchanged
- Hosted sync schema: 1 unchanged
- Portal Action protocol: 14 unchanged

No database migration, player reset, OAuth change, new Render secret, or Web replacement is required.
