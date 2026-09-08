# Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 5

## Treasure Seekers — Solo Venture Progress Repair
- Solo Venture treasure discoveries now record the shared Fellowship activity **`treasure`**.
- **Treasure Seekers** weekly-order progress now advances when a Solo Venture treasure chest is discovered.
- The long-term **Treasure Hunters** deed and any other Fellowship progress keyed to `treasure` advance through the same event.
- Solo treasure events use a run-and-stage-specific idempotency key, so Portal retries/replays cannot double-count progress.
- Progress is credited when the chest is **discovered**, even if the player later retreats or loses unbanked spoils.
- This fix does not fabricate historical weekly-order progress for Solo chests discovered before deployment because the existing aggregate Solo treasure statistic does not preserve enough per-chest timing to backfill a specific order week safely.

## Carried forward from Hotfix 5
- Stream/Rally Ventures remain **100% Encounter / 0% Treasure Chest**.
- Solo Venture remains **80% Encounter / 20% Treasure**.
- Armor and Weapons share the best-first Job-use presentation across Equipment, Current Loadout, item details, and Moogle Emporium Buy/Sell.
- Favorites remain a separate equipment section with **☆ / ★** controls.
- Held gear remains sorted highest item level → lowest; `Replaces X` comparison copy remains removed.

Runtime/frontend `1.7.1-resynthesis-a2h5`; schema **15**; hosted sync **1**; Portal protocol **32**. No migration or player reset.
