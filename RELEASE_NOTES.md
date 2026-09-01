# Crystal Guild v1.6.0 — Gold Saucer RC2

RC2 is the final balance candidate for the complete five-attraction Gold Saucer. It keeps the RC1 feature freeze and fixes the one economy outlier found by the release audit: Mini Cactpot payouts were scaled for a much larger MGP economy than Crystal Guild uses.

## RC2 balance correction

- Mini Cactpot remains **10 MGP** and one ticket per UTC day.
- Its payout table is rescaled to Crystal Guild's 400–6,000 MGP Prize Counter while preserving the familiar sum-value shape.
- Sum **6** remains the headline jackpot at **1,000 MGP**; sum 24 pays 360 MGP and sum 23 pays 180 MGP.
- A random line now averages **36.19 MGP** instead of ~360.35 MGP.
- An optimal four-reveal strategy is about **148.94 MGP expected payout** instead of ~1,484.98 MGP.
- Mini Cactpot now records net **win / draw / loss** relative to its 10 MGP ticket price.

## Other attraction balance — frozen

- Crystal Slots: **87.453%** exact theoretical return; unchanged.
- Monster Toss: best fixed target/style is ~**85.87%** return; unchanged.
- Chocobo Racing: near break-even/slight sink for entry-level birds, modest positive expectation for leveled/favored-trait birds; three daily races keep progression advantage bounded.
- Triple Triad: win pays profit, draw refunds the exact entry cost, loss forfeits the entry; five daily matches keep skill rewards bounded.
- Welcome purse, daily MGP floor, Prize Counter prices, card values, race curves, limits, and all other payouts are unchanged.

See `reports/GOLD_SAUCER_BALANCE_AUDIT_RC2.md` for the full win/draw/loss audit.

## RC1 hardening retained

Monster Toss and Triple Triad entries remain bound to the UTC day on which the persistent game/match starts, including midnight-crossing sessions. Exactly-once settlement, restart persistence, full-card-face Triple Triad values, MGP/Gil separation, and all Gold Saucer UI/recovery hotfixes carry forward.

## Contract

- Runtime: `1.6.0-gold-saucer-rc2`
- Local DB schema: **13**
- Hosted sync schema: **1**
- Portal Action protocol: **29**
- Twitch prefix: `!`
- Gold Saucer currency: **MGP**

There is no database migration or player reset from RC1.
