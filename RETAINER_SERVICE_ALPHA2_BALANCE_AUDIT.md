# Retainer Service Alpha 2 — Targeted Procurement Balance Audit

**Result: PASS.** Alpha 2 trades additional Gil for material certainty without adding reward rolls, reducing assignment time, increasing Retainer EXP, or changing bonus-find odds. Alpha 1 general dispatch prices and progression remain unchanged.

## Focus economy

| Assignment | General | Priority | Premium | Rolls | Guaranteed share | Duration |
|---|---:|---:|---:|---:|---:|---:|
| Field Gathering | 100 Gil | 125 Gil | +25 (25%) | 2 | 50% | 30m |
| Monster Salvage | 250 Gil | 325 Gil | +75 (30%) | 3 | 33% | 1h |
| Mineral Survey | 500 Gil | 625 Gil | +125 (25%) | 3 | 33% | 2h |
| Regional Procurement | 900 Gil | 1,125 Gil | +225 (25%) | 4 | 25% | 4h |
| Specialist Acquisition | 1,500 Gil | 1,875 Gil | +375 (25%) | 4 | 25% | 8h |

A priority selection replaces exactly one normal weighted roll with the selected material. Quantity uses the same normal assignment range (1–2); the remaining rolls use the unchanged route pool. The selected material may still appear again naturally.

## Rarity pressure

All priority choices are restricted to the selected assignment’s existing material pool. No Relic or Artifact material is targetable. The strongest certainty shift occurs on the longest Specialist route: a low-weight rare material can be guaranteed for one normal 1–2 quantity roll, but still requires an 8-hour assignment, Rank 4, 1,875 Gil, and the single active-Retainer slot.

## Resale guardrail

Materials remain normally sellable under the existing 70% material sell ratio. The Retainer is intentionally a procurement service rather than a pure Gil sink, so some advanced routes can recover part or all of their fee if the entire haul is liquidated. The one-assignment timer limits this conversion rate. Worst-case focused expected resale was checked using the highest sell-value target on each route:

| Assignment | Highest-value priority | Expected focused resale* | Priority fee | Approx. net/hour |
|---|---|---:|---:|---:|
| Field Gathering | Goblin Medallion | 139 Gil | 125 Gil | +29 Gil/h |
| Monster Salvage | Chimera Scale | 320 Gil | 325 Gil | -5 Gil/h |
| Mineral Survey | Ironclad Plate | 1,038 Gil | 625 Gil | +206 Gil/h |
| Regional Procurement | Ancient Cloth | 1,276 Gil | 1,125 Gil | +38 Gil/h |
| Specialist Acquisition | Morbol Bulb | 2,218 Gil | 1,875 Gil | +43 Gil/h |

*Expected resale is a conservative economy stress check: it assumes every acquired material is immediately sold and includes the route’s minimum-rank bonus-find chance. It is not the intended use case.

The highest modeled passive conversion is Mineral Survey at roughly +206 Gil/hour when always focusing its highest-sale-value material and liquidating the entire haul. This is bounded by a 2-hour timer and one active Retainer, and is modest relative to active Crystal Guild income. No additional anti-sell restriction is required for Alpha 2.

## Persistence / exploit guardrails

- Reward rolls—including the priority guarantee—are committed at dispatch, before the timer begins.
- Refresh/reconnect/restart cannot reroll the focused haul.
- Only one Retainer assignment can exist at a time.
- Collection and history insertion are idempotent/exactly-once.
- Bonus finds are rolled independently and are not guaranteed by Priority procurement.
- General dispatches remain valid and do not pay the focus premium.

## Conclusion

Alpha 2 is balanced as a **certainty-for-Gil** expansion rather than an output multiplier. Targeting materially improves access to a needed crafting material, but does not increase total base roll count or Retainer progression speed.
