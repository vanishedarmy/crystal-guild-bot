# Crystal Guild v1.6.0 — Gold Saucer Alpha 3

Gold Saucer Alpha 3 makes **MGP** the canonical Gold Saucer currency name without changing any stored balance, attraction cost, payout table, daily allowance, or ordinary Gil behavior.

## MGP contract
- **MGP** replaces the player-facing **SP / Saucer Points** name everywhere in the Bot-side Gold Saucer contract and result messages.
- Existing `player_gold_saucer.points` storage is intentionally retained so live balances require **no database migration**.
- New canonical Portal state fields are `mgp`, `welcome_mgp`, `daily_allowance_mgp`, `account.mgp`, and `records.net_mgp`.
- `currency_name` and `currency_code` both report `MGP`.
- Legacy `points`, `welcome_points`, `daily_allowance_points`, `account.points`, and `records.net_points` remain additive compatibility aliases for an Alpha 2 frontend during rollout.

## Existing Gold Saucer gameplay carried forward
- One-time welcome purse: **500 MGP**.
- Daily floor allowance: **50 MGP** on the first Saucer request of a later UTC day.
- Mini Cactpot: **10 MGP** per daily ticket; payout table unchanged.
- Crystal Slots: **15 MGP** per spin; payout table and cooldown unchanged.
- Monster Toss: **20 MGP** per game, 5 throws, maximum 3 completed games per UTC day; payout tiers unchanged.
- Prize Counter prices are numerically unchanged and now display MGP.
- Gold Saucer remains isolated from ordinary Gil and combat progression.

## Compatibility
- Runtime: `1.6.0-gold-saucer-a3`
- Local DB schema: **12** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **27** unchanged
- Twitch prefix: `!`
- No player reset, OAuth/environment change, new required variable, database migration, payout rebalance, or gameplay reset.

The Alpha 2 Web relay remains protocol-compatible because Alpha 3 adds no new Portal action type. A matching frontend source update is still required wherever the UI hardcodes the old SP/Saucer Points wording.
