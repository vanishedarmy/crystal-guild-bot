# Crystal Guild — V2.12 companion victories (integration candidate)

Based on the complete V2.11 Bot source.

## Changed
- Personal timed Hunt victory uses the existing shared combat snapshot and credits a selected, genuinely owned Beastmaster pet only after an actual damaging Call Beast / King of Beasts assist. The pet receipt is in the Hunt reward transaction.
- Solo Expedition combat victories award one Bond XP receipt per encounter stage, in the existing Bestiary / monsters-defeated transaction. Newly launched expeditions now have a random per-run UUID; old in-progress expeditions remain compatible.
- Dungeon combat room victories award one Bond XP receipt per room, in the same victory transaction. Dungeon run IDs already uniquely identify each run.
- All three modes reuse the V2.11 `award_companion_bond` helper and its existing receipt table: no database schema change (remains 30).
- The companion must be owned, selected in the trusted snapshot, on the Beastmaster job, and have recorded at least one successful damaging pet ability. Defeat, defend-only combat, unowned companions, and duplicate receipts grant nothing.

## Boundaries
- These are Bot **source** changes, not a deployed release.
- No new autonomous pet AI, HP, turns, crafting, or taming source rules.
- The Web V2.11 companion roster patch remains applicable without modification.
- Run full deployment-grade battle, DB backup, Twitch and Portal checks before production.
