# Crystal Guild v1.9.8 — Airship Expedition

This release makes the Guild Airship the second Expedition tier; passive Airship mission launches are replaced by **individual** player trips to three remote sky regions. The original five Chocobo regions, player records, Airship Guild investments and historical mission completion data remain intact.

## Unlocked sky routes

| Region ID for chat | Level | Guild requirement | Region Boss | Unique material |
|---|---:|---|---|---|
| `shattered_sky_isles` | 25+ | Airship constructed | Tempest Roc | Skyglass Shard |
| `aetherstorm_expanse` | 35+ | Crystal Core Tier 1 | Aetherstorm Colossus | Stormheart Crystal |
| `forgotten_dominion` | 45+ | Crystal Core Tier 2 | Dominion Sentinel | Dominion Relic |

The shared Expedition Board must also be complete. A registered Chocobo is **not required** for flying; ground Expeditions **still do** require it. One player cannot have two active Expeditions simultaneously, but Guild members do not block one another's journeys.

## Gameplay effects

- **Hull:** -12% hazard damage per tier, plus improved defeat/retreat salvage retention (+6 percentage points per tier, capped at 90%).
- **Engine:** -12% travel time per tier; reduces emergency landing delays.
- **Cargo Hold:** +1 material on resource and floating-ruin discoveries per tier.
- **Survey Array:** +1.2 percentage points rare-event chance per tier (normal global event cap still applies); +1 exploration point per tier on discoveries; improves floating ruin surveys.
- **Crystal Core:** unlocks additional regions at tiers 1 and 2. Tier 3 remains a Guild investment for future locations.

Airship upgrades are captured at launch. Building or upgrading the Guild ship remains Fellowship-wide; exploring is per-player. The old missions are **no longer launchable**, but prior active missions finish and their history stays recorded. Database schema 27, hosted sync schema 1 and action protocol 39 are unchanged.

## Twitch player commands

`!airship` — Guild ship status

`!airshipregions` — routes, required levels and Crystal Core tiers

`!airshipexpedition shattered_sky_isles scout` — example launch; choose `scout`, `journey`, `deep`, or unlocked `boss`/`legendary` contract

`!airshipstage` — resolve a travel stage when ready

`!airshiproute safe` — choose the next route (`safe`, `unknown`, `deep`) after a stage

`!airshipcamp` — recover between stages

`!airshipreturn` — return safely and bank the carried cache outside combat

`!airshipattack` / `!airshipdefend` / `!airshipretreat` — combat basics

You may also play via the Portal's **Adventure Board > Airship Routes**.

## Installing

1. Back up live Bot and Web databases, original v1.9.7 source/assets, `.env` secrets, tokens and volumes.
2. Apply the Bot source patch and Web source patch **over the parent folder containing Bot/ and Web/**. Or use the full Bot archive **instead of** the Bot patch; do not combine the two Bot options.
3. Do not delete or replace the existing Web/frontend/public art and Web/frontend/dist art. If source art is missing, restore the matching v1.9.7 Web artwork split first.
4. Rebuild Web/frontend from source with `npm ci --include=dev && npm run build`, then deploy Bot and Web together. **Do not serve the stale v1.9.7 dist folder as a v1.9.8 prebuilt release.** Source-build Dockerfile normally handles the rebuild.
5. Restart Bot and redeploy Web. Verify health, version, 3 Airship regions, a ground Expedition, at least one saved flight, a recent mission history entry, and Portal artwork URLs.
6. Roll back to backed-up 1.9.7 code if needed; keep database backups with the deployment. This release introduces no schema changes.

## Validation performed

- Python syntax compilation: passed.
- GameData catalog validation (all new monsters, items, Bestiary overlays, enemy actions): passed.
- New Airship regression tests: passed.
- Existing Expedition regression tests: passed after updating 5-region total assumptions to explicitly count the five original ground regions.
- JSX syntax parse: passed for the changed UI components.
- Full historical Bot test suite: **not verified green**; full run exceeded the execution time budget. Do not treat focused tests as production Twitch/Portal E2E verification.
- Frontend source bundle: **not built in this working environment**; original dependencies contain a Windows-native Rolldown binding and there is no matching Linux binding. Rebuild on your normal frontend build host/CI.

## Limits

New sky-exclusive materials are collectible and persist in normal inventory but are not yet consumed by new sky-specific crafting recipes. This release adds region bosses, hazards and survey events using existing battle mechanics. It does not add new art assets or new browser routes, and it does not claim a tested live Twitch deployment.
