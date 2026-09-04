# Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 2

## Job Quest Unlock Repair

Hotfix 2 fixes advanced Jobs remaining locked even after their Job Quest prerequisites had already been satisfied.

- Ready Job Quests now **complete automatically and retroactively**.
- Reconciliation runs when players open live Jobs state in the Portal, use `!job`, inspect `!jobinfo`, or view `!quests`.
- Existing progress counts: players do **not** need to repeat old Job levels, Hunt clears, monster kills, Ventures, Bestiary progress, or Masteries.
- Quest completion is exactly-once. Gil, titles, transactions, and quest-count achievements cannot be duplicated by repeated refreshes or Job switches.
- The associated advanced Job becomes immediately available after reconciliation; selecting it still creates/uses that Job's normal independent JLv. progression.
- `!quest <name>` remains supported for direct quest inspection/completion.
- Portal Action protocol does not change because the existing `CHARACTER_STATE` request now performs the reconciliation server-side.

Hotfix 1 Encounter Variety protections remain unchanged. Resynthesis and the Alpha 2 Gold Saucer MGP rebalance remain unchanged.

Bot runtime advances to `1.7.1-resynthesis-a2h2`. Paired Web remains `1.7.1-resynthesis-a2`. Local schema **15**, hosted sync **1**, Portal protocol **32**, prefix `!`. No migration or player reset.
