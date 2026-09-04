# Finalization Audit — Crystal Guild v1.7.1 Resynthesis Alpha 2 Hotfix 1

**Decision: PASS — Encounter Variety hotfix.**

The audit identified a selector-pool collapse rather than an incorrect Magic Pot base rarity. Across eight normal Venture regions and 101 encounter-table entries, Magic Pot remains base weight 1. The old Solo Venture near-level filter produced 14 player-level/region states where a region with alternatives collapsed to exactly one preferred monster; Whispering Caverns Lv.24–27 collapsed to Magic Pot.

Hotfix 1 preserves the region rarity tables and instead hardens the selector: minimum candidate variety, a ~45% maximum effective share with 3+ candidates, recent-monster suppression, and a hard stop on a third identical encounter when an alternative exists. Rally Venture, Solo Venture, and Expeditions all participate in the anti-streak weighting; Solo Venture and Expeditions also receive the minimum-pool widening.

Bot runtime `1.7.1-resynthesis-a2h1`; paired Web `1.7.1-resynthesis-a2`; schema **15**; hosted sync **1**; Portal protocol **32**; prefix `!`. No migration or player reset.

Validation: **681/681 Bot**, **562/562 frontend**, **65/65 hosted Web/API**, **120/120 Bot Python**, **16/16 Web Python**, **205/205 JS/MJS**, **843/843 WebP**, **0 public PNG**.

See `ENCOUNTER_VARIETY_AUDIT.md` and `VALIDATION_REPORT.md`.
