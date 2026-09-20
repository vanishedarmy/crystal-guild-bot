# Crystal Guild v1.9.0 Alpha 2 — Economy Balance Finalization Audit

**Decision: PASS.** The economy pass uses targeted corrections instead of blanket nerfs and preserves ordinary progression speed.

## Release contract

- Visible release: **v1.9.0 Alpha 2 — Economy Balance**
- Runtime/frontend: `1.9.0-economy-balance-alpha2`
- Frontend package: `1.9.0-alpha.2`
- Local database schema: **19**
- Hosted sync schema: **1**
- Portal Action protocol: **36**
- Player reset: **not required**

## Final balance decisions

- Keep normal daily Gil, monster rewards, Hunt rewards, bounded Raid pools, shop prices, Forge progression, and resale ratios.
- Keep Trading Post fees at 2% listing / 5% sale tax.
- Correct only the two Retainer routes whose expected NPC liquidation exceeded dispatch cost.
- Raise only the Adamantite Workshop conversion fee needed to eliminate a deterministic resale loop.
- Keep MGP daily credits, Mini Cactpot, Slots, Racing, Triple Triad, and Prize Counter pricing unchanged.
- Buff Monster Toss because it was materially under-rewarding compared with the rest of the Saucer.
- Change the Trading Post activity gate from Expeditions to Ventures so a Level-1 facility does not secretly depend on a Level-6 building.

See `ECONOMY_BALANCE_AUDIT.md` for calculations and rationale.
