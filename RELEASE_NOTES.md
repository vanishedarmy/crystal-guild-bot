# Crystal Guild v1.6.0 — Gold Saucer

## Production release

v1.6.0 promotes the validated RC2 Gold Saucer candidate into production. The complete attraction set is **Mini Cactpot, Crystal Slots, Monster Toss, Chocobo Racing, and Triple Triad**. MGP remains separate from Gil and remains the canonical Saucer currency.

### Final release contents

- Mini Cactpot retains the RC2 Crystal Guild-scaled 10 MGP daily table, including the 1,000 MGP Sum-6 jackpot and net win/draw/loss ledger accounting.
- Crystal Slots, Monster Toss, Chocobo Racing, Triple Triad, Prize Counter pricing, MGP grants, daily limits, and card parameters are unchanged from RC2.
- Monster Toss and Triple Triad daily-entry accounting remains bound to the UTC day on which the paid entry starts.
- Triple Triad keeps the 15-card collection and the artwork-synced canonical Top/Right/Bottom/Left parameters.
- All Gold Saucer actions remain Bot-authoritative and idempotent.

### Release contract

- Runtime: `1.6.0-gold-saucer`
- Local DB schema: **13**
- Hosted sync: **1**
- Portal Action protocol: **29**
- Command prefix: `!`
- Currency: **MGP**

There is no new database migration from RC2 and no player-data reset.
