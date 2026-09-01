# Crystal Guild v1.6.0 — Gold Saucer RC1

RC1 freezes the complete Gold Saucer feature set for release-candidate validation. Mini Cactpot, Crystal Slots, Monster Toss, Chocobo Racing, and Triple Triad are all open; no additional attraction is held back for v1.6.0.

## RC1 hardening

- Monster Toss and Triple Triad daily entries are now consumed on the UTC day the game/match **starts**, not the day a persistent session happens to finish.
- An active same-day Toss/Triad session immediately appears in the daily counter, so the Portal cannot overstate remaining entries.
- A session carried across 00:00 UTC remains charged to its original start day.
- The Triple Triad Open-rules description is release-neutral; gameplay rules are unchanged.
- Exactly-once Portal settlement, restart persistence, MGP/Gil separation, full-card-face values, Chocobo Racing, and all prior Gold Saucer recovery/UI hotfixes carry forward.

## Feature/economy freeze

No MGP grant, entry cost, payout, Prize Counter price, Triple Triad card value, Chocobo Racing curve, or attraction limit is rebalanced in RC1. See `reports/GOLD_SAUCER_BALANCE_AUDIT_RC1.md` for the freeze audit.

## Contract

- Runtime: `1.6.0-gold-saucer-rc1`
- Local DB schema: **13**
- Hosted sync schema: **1**
- Portal Action protocol: **29**
- Twitch prefix: `!`
- Gold Saucer currency: **MGP**

There is no database migration or player reset from Alpha 5 H5/H6.
