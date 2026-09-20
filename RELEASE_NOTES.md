# Crystal Guild v1.9.0 Alpha 1 — Moogle Trading Post

v1.9.0 Alpha 1 introduces the first player-to-player economy service in Crystal Guild: the **Moogle Trading Post**, a Level 1 Fellowship building attached to the Moogle Emporium.

## Fellowship construction

The Trading Post is available as a one-time Level 1 Guild service project requiring:

- Fellowship LVL 1
- 25,000 Gil
- 3 Mythril Ore
- 15 completed Expeditions

Once completed, the Trading Post is permanently available to the Fellowship.

## Player market

- Fixed-price listings; no bidding.
- Eligible gear, materials, consumables, and ordinary items may be listed.
- Listings last 48 hours.
- Maximum 24 active listings per player.
- Listing quantity is capped at 99 and unit price at 1,000,000 Gil.
- A 2% listing fee is charged when an item is posted.
- A 5% tax is removed from completed sales.
- Unsold expired items are automatically returned to the seller.
- Sellers can cancel active listings; the original listing fee is not refunded.

## Progression and item safety

Key/quest-style items, explicitly unsellable items, relic-linked gear, Relic rarity, and Artifact rarity are blocked from the market. The last equipped copy of a piece of gear cannot be listed.

Trading Post mutations are blocked while the acting player is committed to active encounter or raid combat.

## Portal and artwork

The Moogle Emporium now has a third **Trading Post** mode with:

- locked-building construction presentation;
- live market browsing and category filters;
- direct purchase controls;
- listing creation with fee preview;
- personal listing history and cancellation;
- desktop/mobile responsive layouts;
- dedicated Trading Post and Moogle clerk artwork.

## Release contract

- Runtime/frontend: `1.9.0-trading-post-alpha1`
- Frontend visible version: `v1.9.0 Alpha 1`
- Local database schema: **19**
- Hosted sync schema: **1**
- Portal Action protocol: **36**
- No player reset is required.
