# Crystal Guild v1.9.96 — Sovereign Encounters

This cumulative gameplay release builds from v1.9.95 and preserves all existing player progression, high-level equipment, Job Ascension Trials, and Limit Breaks.

## New six-room Ascension Dungeons

- **Abyssal Foundry** — Character Lv.65, recommended Lv.68. First-clear material: Emberglass Core ×3.
- **Void Cathedral** — Character Lv.85, recommended Lv.88. First-clear material: Mirage Hourglass ×3.
- **Throne of Eternity** — Character Lv.99, recommended Lv.99. First-clear material: Eclipse Core ×3.

Existing Forgotten Crystal Sanctum (Lv.55), Celestial Spire (Lv.75), and Astral Crucible (Lv.95) remain available and receive the new encounter rules. The original four early-game Dungeons are unchanged.

## Actual combat mechanics

1. Boss phases activate at **100%, 60%, and 25% remaining HP** in advanced encounters. Phases update enemy pressure and elemental matchups. Players can read current weakness and resistance in the Portal or with `!dungeon`.
2. Correct-element damage deals **40% extra**; resisted elemental damage is reduced **35%**. This is additional only for advanced Dungeon/Trial encounters. Other battles retain their existing weakness behavior. A Job without matching elemental attacks can still win through physical or neutral attacks.
3. Marked enemy attacks occur on scheduled rounds (3 or 4, depending on encounter). The player can see a warning before choosing a turn. **Defend** applies the normal protection plus 40% reduced attack power against the marked strike. Boss statuses still matter.
4. The same system is active in JLv.75, 90 and 99 Job Trials. JLv.60 Trials remain mechanically unchanged. Trial seals and existing requirements are preserved.

## Access

**Portal:** Adventure > Dungeon Board. The enemy panel shows phase name, current elemental affinities, and prominent heavy-attack warnings. Existing Limit Gauge, items, skills and mobile hotbar remain available.

**Twitch chat:** `!dungeon` (show available routes or current battle), `!dungeonstart <id>`, `!dungeoncontinue`, `!dungeonchoose <route>`, `!dungeonaction <attack|defend|ability:id|limit:tier|item:id>`, `!dungeonretreat`. Job Trials retain `!ascension`, `!ascend <level>`, and `!trialaction <action>`. Dungeon round messages include the next enemy intent.

## Compatibility and verification

- No player database schema migration or Portal sync protocol change. Stored Dungeon battles retain the advanced rules in serialized encounter state.
- 178 selected Bot tests and 24 selected frontend tests passed. The new dedicated combat tests cover phase thresholds, weakness/resistance, timed telegraphs, defended damage, and state reload.
- Older Dungeon tests may still assert exactly four total dungeons, the prior release label, or a legacy 16 KB Adventure state limit. Those are historical assumptions, not proofs of a new combat regression. The Portal action result limit is much larger, and transport uses compression where supported.
- Production browser compilation and real Twitch/Portal end-to-end operation are **not** verified in this build environment. Test on staging before live deployment.
