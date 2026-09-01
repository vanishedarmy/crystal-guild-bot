# Gold Saucer RC2 — Win / Draw / Loss Balance Audit

RC2 audits MGP outcomes against each attraction's actual entry cost. A **win** means payout > wager, a **draw** means payout = wager, and a **loss** means payout < wager. Card rewards and cosmetic unlock value are intentionally excluded from MGP return calculations.

## Mini Cactpot — rebalanced in RC2

- Entry: **10 MGP**, one ticket per UTC day.
- RC1 inherited a payout scale that did not fit Crystal Guild's 400–6,000 MGP Prize Counter: a random line returned about **360.35 MGP** on average, while an optimal reveal/line policy was about **1,484.98 MGP** expected payout.
- RC2 scales the payout table to Crystal Guild's economy while preserving the same high/low-sum jackpot shape.
- New jackpot: **1,000 MGP** for sum 6; second-highest outcomes remain 360 MGP (sum 24) and 180 MGP (sum 23).
- Exact random-line expected payout: **36.19 MGP**; net **+26.19 MGP** per daily ticket.
- Exact random-line outcome mix: **44.05% win / 21.43% draw / 34.52% loss**.
- Exact optimal-policy expected payout after the four reveals: **148.94 MGP**; net **+138.94 MGP**. This is intentionally positive because the ticket is daily-limited and rewards informed line choice.
- A 100,000-ticket optimal-policy simulation produced approximately **61.7% win / 17.4% draw / 20.9% loss**.

## Crystal Slots — unchanged

- Entry: **15 MGP** per spin; 5-second cooldown.
- Exact theoretical payout: **13.118 MGP** per spin.
- Return to player: **87.453%**; expected net **-1.882 MGP** per spin.
- Exact net outcome mix: **53.79% win / 0% draw / 46.21% loss**. Pair and triple payouts are always above the 15 MGP wager.
- Slots remain the repeatable long-run MGP sink.

## Monster Toss — unchanged

- Entry: **20 MGP**, three games per UTC day.
- Best fixed target/style by expected MGP remains **Golden Cactuar + Normal Throw**.
- Expected payout for that profile: **17.17 MGP**; return **85.87%**; expected net **-2.83 MGP** per game.
- Net outcome mix for that profile: approximately **43.03% win / 0% draw / 56.97% loss**.
- Lower-risk target/style choices trade expected return for consistency/score control; no payout table change is required for RC2.

## Chocobo Racing — unchanged

Racing is deliberately progression-sensitive rather than flat-RTP gambling. Entry-level birds are near break-even/slight sinks, while leveled birds with favored traits become modest positive-EV racers. Three-race daily limits cap that advantage.

Representative best-choice simulations (200,000 races per case):

| Course | Entry-level, no favored trait | Lv.20 + favored trait |
| --- | ---: | ---: |
| Manderville Sprint (25 MGP) | ~23.96 payout, **-1.04 net** | ~39.39 payout, **+14.39 net** |
| Crystal Circuit (35 MGP) | ~35.16 payout, **+0.16 net** | ~56.40 payout, **+21.40 net** |
| Golden Gauntlet (50 MGP) | ~49.10 payout, **-0.90 net** | ~69.77 payout, **+19.77 net** |

First and second place are net wins; third place is a partial-return loss; fourth through sixth return 0 MGP. This preserves meaningful podium tiers without making early racing a guaranteed source of MGP.

## Triple Triad — unchanged

Triple Triad has no hidden RNG in the base ruleset: outcome depends on the player's deck and placement decisions against deterministic NPC logic. Draw payouts exactly return the entry fee.

| Opponent | Cost | Win payout / net | Draw payout / net | Loss payout / net | Break-even win rate if no draws |
| --- | ---: | ---: | ---: | ---: | ---: |
| Saucer Attendant | 20 | 50 / **+30** | 20 / **0** | 0 / **-20** | 40.0% |
| Card Shark | 30 | 80 / **+50** | 30 / **0** | 0 / **-30** | 37.5% |
| Crystal Master | 45 | 130 / **+85** | 45 / **0** | 0 / **-45** | 34.6% |

The increasingly favorable skilled-player return is intentional: tougher opponents require win unlocks and stronger collected cards, and play is capped at five entries per UTC day.

## RC2 decision

**Only Mini Cactpot is rebalanced.** Slots, Monster Toss, Chocobo Racing, Triple Triad, daily limits, welcome/daily MGP grants, and Prize Counter prices remain frozen. The Cactpot correction removes the single economy outlier while preserving distinct attraction identities: daily jackpot, repeatable sink, carnival skill-risk, companion progression, and deterministic card skill.
