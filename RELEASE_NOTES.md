# Crystal Guild v1.6.0 — Gold Saucer Alpha 4 — Chocobo Racing

Gold Saucer Alpha 4 opens **Chocobo Racing** using each player's existing registered Chocobo. It preserves the Alpha 3 MGP contract and every existing Gold Saucer balance, payout table, Prize Counter purchase, and record.

## Chocobo Racing
- Uses the Chocobo already registered through the existing Stable; no duplicate companion system is created.
- **3 races per UTC day**, resetting at 00:00 UTC.
- Three courses:
  - **Manderville Sprint** — Bond Lv. 1+, 25 MGP entry; podium 70 / 40 / 20 MGP.
  - **Crystal Circuit** — Bond Lv. 5+, 35 MGP entry; podium 110 / 55 / 25 MGP.
  - **Golden Gauntlet** — Bond Lv. 10+, 50 MGP entry; podium 160 / 75 / 35 MGP.
- Three race paces: **Steady Pace**, **Balanced**, and **Final Sprint**. They trade consistency against upside rather than guaranteeing placement.
- Existing Bond level provides a modest performance curve. Existing Chocobo traits receive a small course-favored bonus.
- Six-racer outcomes are committed by the authoritative Bot in one idempotent Portal action. Duplicate action delivery replays the same result without a second entry charge or payout.

## Records and rewards
- Saucer Ledger adds races, wins, podiums, win rate, best finish, and best race payout.
- Race activity is stored in the existing Gold Saucer history ledger.
- Prize Counter adds cosmetic titles **Feathered Finisher** and **Circuit Champion**.
- Racing awards MGP only; it does not create Gil, items, combat stats, or a separate Chocobo progression track.

## Compatibility
- Runtime: `1.6.0-gold-saucer-a4`
- Local DB schema: **12** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **28** (new `CHOCOBO_RACE` action)
- Twitch prefix: `!`
- MGP remains canonical; legacy Alpha 2 balance aliases remain available for compatibility.
- No player reset, OAuth/environment change, new required variable, or database migration.
