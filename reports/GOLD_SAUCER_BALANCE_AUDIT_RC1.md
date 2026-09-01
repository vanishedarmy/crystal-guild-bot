# Gold Saucer RC1 Balance Audit

Audit-only freeze check for v1.6.0 RC1. No entry cost, payout, MGP grant, Prize Counter price, or card value is changed by this report.

- Welcome purse: **500 MGP**
- Daily floor allowance: **50 MGP**
- Currency remains isolated from Gil.

## Mini Cactpot
- Cost: **10 MGP**
- Random-line baseline average payout: **360.35 MGP**.
- Payout range: **36–10,000 MGP**. Actual play can choose among revealed-line options, so this is not the strategic EV.

## Crystal Slots
- Cost: **15 MGP**
- Exact enumerated average payout: **13.1180 MGP**.
- Exact return: **87.453%**, consistent with the configured ~87.5% target.
- Outcome probabilities: triple **5.33%**, pair **48.46%**, miss **46.21%**.

## Monster Toss
- Cost: **20 MGP**; **3 games/day**.
- Highest fixed-choice average payout among the 12 target/style combinations is **17.17 MGP** (golden_cactuar + normal), an average net sink of **-2.83 MGP** per game.
- Player mixing of targets/styles can alter variance; RC1 does not rebalance the payout table.

## Chocobo Racing
- Three races/day. Monte Carlo confirms intended progression: minimum-Bond/no-favored-trait profiles hover around break-even or modest sinks, while high-Bond favored-trait racers become positive expected MGP sources.
- This progression curve is frozen for RC1; no course cost or podium payout changes.

## Triple Triad
- Five matches/day.
- Draw payouts equal entry cost at every opponent tier.
- If draws are ignored, win-only break-even rates are: **saucer_attendant 40.0%**, **card_shark 37.5%**, **crystal_master 34.6%**.

## RC1 Decision
- **No economy rebalance.** Existing Alpha 5 H5/H6 MGP values are frozen into RC1.
- RC1 changes only daily-entry accounting for persistent Monster Toss/Triple Triad sessions so an entry belongs to its UTC start day.
- Schema **13**, hosted sync **1**, Portal protocol **29**.
