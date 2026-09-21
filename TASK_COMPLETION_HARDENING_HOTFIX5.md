# Crystal Guild v1.9.0 Alpha 6 — Progress Accounting Hardening Hotfix 5

This hotfix strengthens task-completion accounting across Fellowship construction, Weekly Orders, Deeds, and Airship missions.

## Canonical progress rules

- **Monsters defeated** counts any valid Bestiary monster kill, regardless of whether it comes from a normal encounter, Hunt, Venture, Solo Venture, Expedition, Dungeon, or World Event.
- **Combat victories** counts all of those victories plus Raid victories.
- **Source-specific requirements** remain strict: Hunts won, Raid clears, Ventures completed, Expeditions completed, crafting, forging, and similar named requirements only advance from their matching source.
- Raid bosses are combat victories but are not counted as Bestiary monster defeats.

## Hardening details

- Solo Venture, Expedition, and Dungeon combat now emit canonical `monster_victory` receipts when the authoritative Bestiary/player defeat counters advance.
- Receipt keys are replay-safe, so retrying the same resolved victory cannot advance construction twice.
- Fellowship project requirements, Weekly Orders, Deeds, and Airship mission progress now share one activity-semantic matcher.
- Airship missions use the strongest matching weight rather than adding alias weights together, preventing a Hunt from counting twice as both a Hunt and a generic combat victory.

No database migration or player reset is required. Schema remains 19 and Portal Action protocol remains 36.
