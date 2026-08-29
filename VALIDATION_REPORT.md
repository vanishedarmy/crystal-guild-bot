# Crystal Guild v1.3.0 — Guild Expansion Alpha 3 Validation Report

## Result
**PASS**

## Automated regression suites
- Bot Python unittest suite: **458 / 458 PASS**.
- Frontend Node regression suite: **333 / 333 PASS**.
- Hosted Web/API Python suite: **47 / 47 PASS**.
- Focused Guild Expansion Alpha 3 service suite: **5 / 5 PASS**.

## Alpha 3 service coverage
- Workshop Lv. 2 services unlock the two basic refining exchanges.
- Workshop Lv. 3 unlocks Adamantite and Dark Matter conversion.
- Workshop material/Gil deductions and output grants are transactional.
- Portal Workshop exchanges are replay-safe and cannot duplicate a completed exchange after retry.
- Workshop service access is blocked during incompatible active combat/persistent Adventure states.
- Chocobo Stable XP bonuses scale +5% / +10% / +15% across major facility Lv. 1–3.
- Guild Archive Expedition rare-event bonus scales 0 / +0.5 / +1.0 percentage point across Lv. 1–3 and remains under the existing rare-event ceiling.
- `FELLOWSHIP_STATE` publishes facility-service data needed by the signed-in Portal.
- Hosted `WORKSHOP_EXCHANGE` validation accepts only `exchange_id` plus 1–20 `batches`.
- Web and Bot agree on Portal Action protocol **21**.

## Source and artwork validation
- Python compile sweep: **84 / 84 PASS**.
- JavaScript/MJS `node --check`: **139 / 139 PASS**.
- Explicit routed artwork references checked: **221**; missing: **0**.
- Twitch command prefix contract remains `!`.

## Upgrade/continuity
- Alpha 3 is additive on the Alpha 2 database.
- Local DB schema remains **8**; no migration is required.
- Hosted sync schema remains **1**.
- Portal Action protocol advances **20 → 21**, so the Alpha 3 Web and Bot must be deployed together.
- Existing player progression, inventories, Chocobo state, Expedition state, Fellowship Renown, facility tiers, project progress, Weekly Order history, and Guild Rank remain in place.

## Packaging verification
- Alpha 2 → Alpha 3 Bot patch: **21 changed/new files, 0 deleted**; exact reconstruction of **139 / 139** final Bot files.
- Alpha 2 → Alpha 3 Web patch: **39 changed/new files, 0 deleted**; exact reconstruction of **798 / 798** final Web files.
- Full Bot/Web/Complete archives match the finalized source trees exactly.
- ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations** across all release archives.
- SHA-256 manifest verification: **PASS**.

## Compatibility
- Bot runtime: `1.3.0-guild-expansion-a3`
- Hosted Web runtime: `1.3.0-guild-expansion-a3`
- Frontend asset revision: `1.3.0-guild-expansion-a3`
- Local DB schema: **8**
- Hosted sync schema: **1**
- Portal Action protocol: **21**
- Twitch prefix: `!`
- Player reset: **none**
- OAuth changes: **none**
- New environment variables: **none**
