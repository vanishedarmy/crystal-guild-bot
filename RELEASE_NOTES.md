# Crystal Guild v1.2.0 — Expeditions Beta 1

## Balance & Simulation

Beta 1 freezes the Expeditions feature set and validates the Alpha 5 loop through reproducible simulation, route-risk tuning, and economy checks. No new progression system or currency is introduced.

### Route risk now changes actual pressure
- **Safe Route:** 90% combat pressure and 82% hazard damage, alongside its existing lower event/reward weighting.
- **Unknown Route:** neutral 100% combat pressure and 100% hazard damage.
- **Push Deeper:** 110% combat pressure and 115% hazard damage, alongside its existing +20% route reward multiplier, stronger rare-event chance, and rare-monster weighting.

The intent is simple: Safe should be a real survival choice, Unknown the neutral baseline, and Push Deeper a visibly stronger but riskier reward play.

### Legendary Contract smoothing
Legendary Regional Contracts remain the repeatable Expedition endgame, but their final boss scaling is slightly eased from the Alpha-era stack. Legendary boss HP is now 120% of the underlying Regional Boss instead of 125%, and its base pressure modifier is 1.10 before route pressure instead of 1.15. Route choice therefore matters at the Legendary boss itself.

### Reproducible balance matrix
The release includes `tools/simulate_expedition_balance.py` plus fixed-seed JSON/Markdown reports covering **3,000 simulated Expeditions**:
- five representative player level bands;
- Scout, Journey, and Deep Expedition depths;
- Safe, Unknown, and Push Deeper routes;
- all five Regional Boss Contracts;
- all five Legendary Contracts.

The simulator deliberately uses basic Attack combat and conservative automatic Camp behavior, so it acts as a survival-pressure floor rather than a prediction of optimized player play with abilities and battle items.

Aggregate standard-route completion in that conservative matrix:

| Depth | Safe | Unknown | Push Deeper |
|---|---:|---:|---:|
| Scout | 99.5% | 99.5% | 95.5% |
| Journey | 97.0% | 95.0% | 85.5% |
| Deep Expedition | 96.5% | 89.0% | 69.5% |

Contract aggregate completion in the same baseline:

| Contract | Safe | Unknown | Push Deeper |
|---|---:|---:|---:|
| Regional Boss | 76.5% | 60.0% | 44.5% |
| Legendary | 52.0% | 20.5% | 13.5% |

### Economy guardrail
Alpha 5 Hunt Seal completion stipends remain unchanged: Scout 2, Journey 4, Deep 7, Regional Boss 10, Legendary 15. The simulation/economy audit keeps Expeditions as a secondary Hunt Seal source rather than replacing dedicated Hunts.

### Portal & Guide
The Expedition route chooser now states the practical risk difference directly: Safe reduces combat/hazard pressure; Push Deeper increases it. What's New and the Player Guide document Beta 1 while retaining Alpha 2–5 history. The new pressure constants remain Bot-authoritative so the compact Adventure state stays below its established 16 KB guardrail.

## Compatibility
- Bot runtime: `1.2.0-expeditions-b1`
- Hosted Web runtime: `1.2.0-expeditions-beta1`
- Frontend asset revision: `1.2.0-expeditions-b1`
- Local DB schema: **8** (unchanged)
- Hosted sync schema: **1** (unchanged)
- Portal Action protocol: **20** (unchanged)
- New environment variables: **none**
- OAuth changes: **none**
- Player reset/database migration: **none**
