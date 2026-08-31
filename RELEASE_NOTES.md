# Crystal Guild v1.6.0 — Gold Saucer Alpha 2

Gold Saucer Alpha 2 opens **Monster Toss** as the third playable Saucer attraction while carrying Mini Cactpot, Crystal Slots, Prize Counter, H1 scenic artwork, and Alpha 1 Hotfix 2 UX/records behavior forward.

## Monster Toss
- **20 SP** entry per game.
- **5 throws** per game and **3 completed games per UTC day**.
- Choose one of four targets each throw: Small Pot, Medium Pot, Large Pot, or Golden Cactuar.
- Choose Safe, Normal, or Power throw style to trade hit chance against score.
- Active game ID, score, throw count, and throw history persist across Portal refreshes, reconnects, and Bot restarts.
- Every start/throw uses Portal action replay receipts; duplicate delivery returns the committed result instead of charging or throwing twice.
- Final score maps to a bounded SP reward tier; Monster Toss never uses ordinary Gil.

## Records & prizes
- Adds Monster Toss games, best score, hit accuracy, total throws/hits, and best payout to the personal Saucer Ledger.
- Adds cosmetic-only Prize Counter titles **Toss Tactician** and **Pot Shot Pro**.
- Existing Cactpot and Slots payout tables are unchanged.

## Compatibility
- Runtime: `1.6.0-gold-saucer-a2`
- Local DB schema: **12**
- Hosted sync schema: **1**
- Portal Action protocol: **27**
- Twitch prefix: `!`
- Schema 12 is additive and contains only persistent Monster Toss active-game state.
- No player reset, OAuth/environment change, new required environment variable, Gil economy change, combat progression change, Cactpot payout change, or Crystal Slots payout change.
