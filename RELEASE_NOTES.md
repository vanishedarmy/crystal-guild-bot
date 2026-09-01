# Crystal Guild v1.7.0 — Retainer Service Alpha 2

Alpha 2 expands the personal Retainer Service with **targeted procurement** and a persistent recent-haul record. Every existing assignment can still run as the Alpha 1 general mixed haul, or the player can nominate one material from that route as a priority.

A focused dispatch costs a modest Gil premium and guarantees one normal reward roll for the selected material. Remaining rolls and bonus finds stay mixed and independent, preventing priority procurement from becoming a rare-material multiplier. General assignment costs, durations, Retainer EXP, Rank thresholds, one-assignment limits, dispatch-time reward commitment, and exactly-once collection are unchanged.

The Retainer desk now records the eight most recently collected assignments with route, priority, haul, bonus find, Gil cost, and Retainer EXP.

Database schema advances from **14 to 15** for Retainer history. Portal Action protocol advances from **30 to 31** because `RETAINER_DISPATCH` now accepts an optional `priority` material ID. Hosted sync remains 1. No artwork changes are included in Alpha 2; Retainer artwork is intentionally the next pass.

Runtime identity: `1.7.0-retainer-a2`.
