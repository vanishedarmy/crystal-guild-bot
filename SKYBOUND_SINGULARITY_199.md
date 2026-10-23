# Crystal Guild v1.9.9 — Skybound Singularity

## What's added

This update expands **3 existing Airship Expedition regions to 6 total** and adds **1 separate World Map SuperBoss region beyond Omega Ruins**. It includes **7 new location backdrops**, one for each existing and new Airship region plus the new endgame world region.

| Region | Type | Minimum level | Crystal Core | Guardian |
|---|---|---:|---:|---|
| Shattered Sky Isles | Existing Airship | 25 | 0 | Tempest Roc |
| Aetherstorm Expanse | Existing Airship | 35 | 1 | Aetherstorm Colossus |
| Forgotten Dominion | Existing Airship | 45 | 2 | Dominion Sentinel |
| **Emberglass Caldera** | New Airship | 55 | 2 | Emberglass Wyrm |
| **Frostveil Observatory** | New Airship | 65 | 3 | Frostveil Astrolabe |
| **Gilded Mirage Expanse** | New Airship | 75 | 3 | Mirage Pharaoh |
| **Eclipsed Singularity Citadel** | New World Map region | 97 | Not an Airship route | Eclipse Sovereign — Ultimate Superboss raid |

The Citadel includes two new high-level regional monsters, **Eclipse Harbinger** and **Singularity Archon**. The Eclipse Sovereign raid has 1,350,000 HP, four phases and higher attack pressure than the previous ultimate raid bosses. New expedition bosses provide guaranteed region materials upon successful contracts. New materials are collectible, but this update does not add new crafting recipes for them.

## Download and install — normal folder tree, no multipart joins

Two ZIP files; each contains an ordinary `Bot/` or `Web/` tree.

1. **Back up your current Bot, Web, database/state volumes, and any secrets**. Keep `.env` files and production databases safe.
2. Extract **Bot_Full.zip** into the **parent folder of Bot/**, merging/overwriting the matching source files. **Do not delete the existing Bot folder or database files**. The archive does not contain live `.env` or database data.
3. Extract **Web_Source_Artwork_Update.zip** into the **parent folder of Web/**, merging/overwriting matching source files and adding the seven WebP assets. **Do not delete `Web/frontend/public`**: the update intentionally preserves all earlier artwork and adds only the seven new region illustrations. The Web archive includes the latest v1.9.8 Portal repair source as well as v1.9.9 changes.
4. Rebuild the frontend from `Web/frontend` using your usual deployment/CI environment (`npm ci --include=dev` then `npm run build`). Redeploy both Bot and Web. A stale prebuilt `dist` folder is **not** included as a production build.
5. Verify that the Expedition Board offers **6 Airship regions**, a newly selected region shows its background, all six regions can be unlocked appropriately, and the World Map offers the level-gated Citadel with its artwork.

**Never extract either ZIP into Bot/ or Web/ themselves**; both archives already include that top-level directory name.

## Where to play

- Airship chat: `!airshipregions`; launch with `!airshipexpedition emberglass_caldera scout`, `!airshipexpedition frostveil_observatory scout`, or `!airshipexpedition gilded_mirage_expanse scout`.
- SuperBoss World Map: reach Lv.97, then `!travel eclipsed_singularity_citadel`; enemies in the region are stronger than Omega Ruins.
- Ultimate raid: `!bossinfo Eclipse Sovereign`, then streamer/mod command `!spawnboss Eclipse Sovereign` when ready for a Guild raid.
- Portal: Adventure Board → Airship Routes; World Map → Travel Regions. No new URL route is required.

## Artwork paths

Six Airship backdrops are saved under `Web/frontend/public/expeditions/airship-<region-id-with-hyphens>.webp`, and are referenced by the region cards and selected/active Expedition Board background in the Portal stylesheet.

Citadel artwork: `Web/frontend/public/retro-phase-ii/regions-hd/eclipsed_singularity_citadel.webp`. The World Map's existing dynamic art routing automatically references this path.

## Verification and caveats

- GameData comprehensive static validation: **passed (0 errors)**.
- New v1.9.9 engine regression tests: **passed** for gates, level checks, world travel, region catalogs, and raid registration.
- Existing airship and Chocobo Expedition regression tests: **passed**, with catalog-size expectations updated.
- Focused Bot regression selection: **72 passed**. Bestiary integration/research tests: **20 passed** after extending catalog expectations.
- New Web artwork integration tests: **3 passed**; all seven illustrated WebP files are present, their file formats and stylesheet/World Map references checked.
- The legacy comprehensive test run is **not fully green**: 1,063 tests ran with 34 failures, predominantly older version-number contracts (many still expect v1.9.7), pre-1.9.8 retired Airship mission behavior, static Bestiary totals, and historic compact-payload budgets. Some catalog assertions have been updated for v1.9.9. Do not interpret this as a verified end-to-end production deployment.
- A complete frontend production build and live Twitch/Portal deployment **were not performed in this workspace**; run your standard build and deployment validation.
- No new database migration, persistent state format, or frontend action protocol has been introduced. Existing region IDs and save data remain intact.
