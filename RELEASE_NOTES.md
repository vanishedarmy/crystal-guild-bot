# Crystal Guild v1.6.0 — Gold Saucer Alpha 5 — Triple Triad

## Triple Triad
- Opens Triple Triad as the fifth playable Gold Saucer attraction.
- Grants a five-card starter collection and saved five-card deck on first entry.
- Adds a 15-card collection and three NPC opponents: Saucer Attendant, Card Shark, and Crystal Master.
- Uses the Alpha 5 Open ruleset: higher touching side captures the lower adjacent card. Same, Plus, elemental, and regional rules are intentionally deferred.
- Allows five completed matches per UTC day. Match state persists across refreshes and Bot restarts.
- MGP entry costs and payouts are authoritative and exactly-once. Winning can award the first still-unowned card from that opponent's reward pool.
- Standard ten-point scoring includes cards still held in hand, allowing legitimate draws.

## Gold Saucer
- Adds Triple Triad matches, wins, cards owned/won, and streak records to the Saucer ledger contract.
- Adds cosmetic Prize Counter titles `Triad Tactician` and `Card Hall Master`.
- `!saucerreset` now also clears an active Triple Triad match while preserving the player's MGP, card collection, saved deck, and records.
- Existing Mini Cactpot, Crystal Slots, Monster Toss, Chocobo Racing, and MGP balances/economics are preserved.

## Compatibility
- Runtime: `1.6.0-gold-saucer-a5`
- Local DB schema: **13**
- Hosted sync schema: **1**
- Portal Action protocol: **29**
- Twitch prefix: `!`
- No player reset, MGP conversion, OAuth change, or new required environment variable.
