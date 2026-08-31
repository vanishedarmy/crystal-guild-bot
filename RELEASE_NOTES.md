# Crystal Guild v1.6.0 — Gold Saucer Alpha 1

Gold Saucer Alpha 1 opens Crystal Guild's first dedicated attraction hall without changing the existing combat, Relic, Dungeon, Trial/Raid, Expedition, Fellowship, Chocobo, crafting, or normal Gil economies.

## Gold Saucer foundation
- Adds a private **Saucer Point (SP)** account for every adventurer.
- First Gold Saucer visit grants **500 SP** exactly once.
- Starting on the next UTC day, the first Saucer visit each day grants a **50 SP floor allowance** so a zero-balance player can always recover access without touching Gil.
- SP cannot be purchased with Gil or real money and is not convertible back into Gil.
- Tracks lifetime SP earned/spent plus attraction records and recent ledger activity.

## Prize Counter
- Adds an Alpha 1 cosmetic-only Prize Counter.
- **Saucer Regular** — 400 SP.
- **Cactpot Connoisseur** — 1,200 SP.
- **Jackpot Chaser** — 2,500 SP.
- Prize purchases are atomic, replay-safe, and unlock existing Title-system records only; no combat stats, Gil, items, or progression power are sold.

## Mini Cactpot
- One persistent daily ticket costing **10 SP**.
- One cell is revealed automatically; the player reveals three more cells.
- The player then chooses one of eight rows/columns/diagonals and receives the sum-based payout.
- Ticket grid, reveals, state, choice, and result persist through Portal refreshes, reconnects, and Bot restarts.
- Duplicate Portal delivery replays the committed result instead of charging or paying twice.

## Crystal Slots
- Quick three-reel attraction costing **15 SP** per spin.
- Six weighted symbols, bounded pair/triple payouts, and a short server-authoritative cooldown.
- Every spin is replay-safe and recorded in the Saucer ledger.

## Portal & roadmap
- Adds a dedicated **Gold Saucer** tab to each character profile.
- Adds personal balance, Mini Cactpot board, Crystal Slots, Prize Counter, recent activity ledger, records, and attraction roadmap.
- **Monster Toss**, **Chocobo Racing**, and **Triple Triad** are visible as Coming Soon and are not partially enabled in Alpha 1.
- Chocobo Racing is reserved to use the existing registered Chocobo system in a later Alpha.

## Streamer controls
- `!saucergrant <player> | <amount>` grants bounded test/event SP.
- `!saucerreset <player>` clears an active ticket and Saucer cooldowns while preserving balance and records.
- Matching controls are available from the Streamer Dashboard.

## Compatibility
- Runtime: `1.6.0-gold-saucer-a1`
- Local DB schema: **11** (additive migration with verified pre-migration backup)
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **26**
- Twitch prefix: **`!`** unchanged
- No player reset, OAuth reauthorization, new required environment variable, or hosted sync migration.
