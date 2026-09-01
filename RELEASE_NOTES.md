# Crystal Guild v1.6.0 — Gold Saucer Alpha 5 Hotfix 5 — Triple Triad Full Card Face Sync

Hotfix 5 makes the finished Triple Triad card faces authoritative both visually and numerically. The Web now shows the complete card face without duplicate UI stat overlays, and the Bot values are synchronized to the numbers printed on those cards.

## Authoritative value corrections
- Chocobo: **3 / 4 / 2 / 1** (Top / Right / Bottom / Left)
- Moogle: **2 / 3 / 4 / 3**
- Cactuar: **5 / 2 / 1 / 5**
- Bomb: **4 / 2 / 6 / 2**
- Flan: **1 / 5 / 4 / 3**

The remaining ten cards already matched their artwork and are unchanged.

## Contract
- Runtime: `1.6.0-gold-saucer-a5h5`
- Local DB schema: **13**
- Hosted sync schema: **1**
- Portal Action protocol: **29**
- Prefix: `!`
- Currency: **MGP**

No schema migration, MGP rebalance, collection reset, deck reset, or action-contract change is required. Existing active matches resume with the corrected card definitions after deployment.
