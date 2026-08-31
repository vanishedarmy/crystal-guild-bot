# Crystal Guild v1.6.0 — Gold Saucer Alpha 1 Hotfix 2

Alpha 1 Hotfix 2 is the Gold Saucer UX, animation, records, and balance-polish pass. It carries the Alpha 1 feature set and Web Hotfix 1 visual treatment forward while leaving the normal Gil economy, combat progression, Prize Counter costs, Mini Cactpot payout table, and Crystal Slots payout table unchanged.

## Gold Saucer polish
- Mini Cactpot now schedules each newly opened ticket to the next **00:00 UTC** reset instead of 24 hours from the opening time.
- The authoritative state exposes the resolved Cactpot line sum and a bounded result tier for clearer Portal presentation.
- Crystal Slots results now expose net SP and a presentation tier; the server still commits every result before any client animation.
- Gold Saucer records are derived from the existing transaction ledger: net SP, games played, Slot win rate, realized Slot return, pair/triple/miss counts, Cactpot total payout, and Cactpot high-roll count.
- The validated Slots payout table remains unchanged at approximately **87.5% long-run expected return** for a 15 SP spin.

## Compatibility
- Runtime: `1.6.0-gold-saucer-a1h2`
- Local DB schema: **11** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **26** unchanged
- Twitch prefix: `!`
- No H2 database migration, player reset, OAuth/environment change, new required variable, Gil economy change, or combat balance change.
