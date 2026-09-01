# Crystal Guild v1.6.0 — Gold Saucer Alpha 5 Validation Report

## Result
**PASS**

## Regression
- Bot: **631 / 631 PASS**.
- Focused Alpha 5 Triple Triad: **8 / 8 PASS**.

## Alpha 5 coverage
- Runtime `1.6.0-gold-saucer-a5`, schema 13, hosted sync 1, Portal protocol 29.
- Additive schema 12→13 migration and verified pre-schema backup behavior.
- Starter collection/deck, owned/unique deck validation, opponent gates, daily match limit, persistent match resume, capture rules, standard ten-point scoring, MGP settlement, card rewards, exactly-once replay, worker validation, and streamer reset preservation.
- Existing Gold Saucer, Dungeon, Expedition, Guild, Trial/Raid, combat, item, Chocobo, Fellowship, recovery, and migration regressions remain green.

## Source gate
Matched Bot + Web Python source parse is **121 / 121 PASS**. See the Web validation report for frontend parser, CSS, asset, hosted API, and production-build gates.
