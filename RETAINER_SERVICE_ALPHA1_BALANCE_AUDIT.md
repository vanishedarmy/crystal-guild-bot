# Retainer Service Alpha 1 — Procurement Balance Audit

## Design target

Retainer Service is a supplemental crafting-material path and a recurring Gil sink. It must not replace Hunts, Expeditions, Dungeons, Trials, Workshop refining, or prestige drops. Alpha 1 therefore permits one assignment at a time, uses category-based pools rather than exact-item orders, and excludes Relic/Artifact materials.

## Assignment economy

| Assignment | Rank | Time | Gil | EXP | Base expected material qty | Min-rank bonus chance | Expected qty incl. bonus | Approx. Gil / material |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Field Gathering | 1 | 30m | 100 | 20 | 3.00 | 6% | 3.06 | 32.7 |
| Monster Salvage | 1 | 1h | 250 | 35 | 4.50 | 6% | 4.56 | 54.8 |
| Mineral Survey | 2 | 2h | 500 | 65 | 4.50 | 7% | 4.57 | 109.4 |
| Regional Procurement | 3 | 4h | 900 | 110 | 6.00 | 8% | 6.08 | 148.0 |
| Specialist Acquisition | 4 | 8h | 1,500 | 180 | 6.00 | 9% | 6.09 | 246.3 |

Longer assignments intentionally become less Gil-efficient per material because their pools move toward uncommon/rare crafting stock. The value proposition is access and convenience, not raw quantity.

## Weighted rarity profile at minimum unlock rank

- Field Gathering: ~92% common / 8% uncommon by pool weight.
- Monster Salvage: ~54% common / 46% uncommon.
- Mineral Survey: ~25% common / 26% uncommon / 49% rare.
- Regional Procurement: ~75% uncommon / 25% rare.
- Specialist Acquisition: 100% rare crafting materials.
- Relic and Artifact rarity: **0% in every Alpha 1 pool**.

## Rank pacing

A direct progression path using newly unlocked routes reaches Master only after substantial elapsed assignment time. One representative minimum-rank path is 5 Field Gatherings → 4 Mineral Surveys → 4 Regional Procurements → 4 Specialist Acquisitions, totaling about **58.5 hours of assignment time**, **17 completed assignments**, and **12,100 Gil** before reaching the 1,400 EXP Master threshold.

## Decision

**PASS for Alpha 1.** The system creates a useful passive material route while preserving active-content value. No exact material is guaranteed, one assignment is allowed at a time, higher-tier access is time/rank gated, and prestige material rarity remains excluded. Live Alpha telemetry should be reviewed before widening pools or adding a second simultaneous Retainer.
