# Balance Audit — Moogle Emporium Annex Alpha 3

## Result

**PASS — bounded convenience expansion.**

The Annex changes shop breadth, not purchasing power. It adds three visible stock choices after a one-time Guild construction project; every item still costs its normal Gil price and remains subject to existing level/job eligibility and weighted selection.

## Construction cost

- Fellowship LVL 3
- 20,000 Gil
- 12 Mythril Ore
- 20 crafted items

The project is deliberately smaller than late Guild construction and large community initiatives. It is substantial enough to require shared participation but early enough to act as a practical v1.7 service expansion.

## Shop impact

- Base rotation: 9 slots
- Annex rotation: 12 slots
- Added slots: +3 (+33.3% visible choices)
- Prices: unchanged
- Sell values: unchanged
- Refresh timer: unchanged
- Level/job gates: unchanged
- Per-pick rarity weights: unchanged
- Free items/currency: none

Three extra weighted picks naturally increase the chance that a player sees a desirable item somewhere in a rotation. That broader access is the explicit value of constructing the Annex. The effect remains bounded by one personal rotation, normal purchase prices, no duplicate stock IDs, and existing eligibility rules.

## Exploit review

The Annex does not create Gil, items, MGP, Retainer rewards, or additional refreshes. It cannot bypass combat transaction locks or normal purchase validation. Cached stock is rerolled only when its slot count no longer matches the current Guild capacity, preventing stale nine-slot rotations after construction without creating a manual reroll exploit.
