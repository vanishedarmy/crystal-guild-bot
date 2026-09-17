# Crystal Guild v1.8.0 RC1 — Merc Service

RC1 hardens the Alpha 2 Merc Service without adding new feature scope.

- Deployed Heroes and their Hunt / Venture / Raid slots remain unavailable until the active assignment resolves.
- Deployed contracts cannot be cancelled or rehired mid-mission.
- Timed Hunt deployment state survives runtime checkpoint recovery.
- A Solo Venture that fails during pre-start setup restores the already-paid Merc reservation.
- Alpha 2 Hunt Seal pricing, Hero signature effects, three independent slots, artwork, and availability rules remain unchanged.

Release contract: runtime `1.8.0-merc-rc1`, local schema **17**, hosted sync **1**, Portal Action protocol **34**, no player reset.
