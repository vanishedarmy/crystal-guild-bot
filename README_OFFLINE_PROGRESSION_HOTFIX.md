# Crystal Guild — Offline Progression Hotfix

## Baseline

This hotfix is built for the active pre–Living World Crystal Guild line:

- Bot gameplay line through the v1.9.4.6 Seasonal Ventures update.
- Web Portal line through v1.9.4.7 Portal Usability Overhaul + Gold Saucer layout hotfix.
- Living World Batch 1A / 1B is **not** included.

## Goal

No Guild upgrade, construction path, Airship upgrade, or shared long-term advancement gate requires Raid participation, a Raid win, a live Stream Venture, or any other live-stream-only activity. All infrastructure progression can be completed through offline-capable Portal gameplay.

Raids remain available as optional live activities and can still have their own trophies, achievements, records, and moments. Those optional Raid records do not gate Guild infrastructure or upgrade progression.

## Progression changes

| Former live-only gate | Offline replacement |
| --- | --- |
| Guild Hall Raid-clear requirements | Hunt wins |
| Airship Dock Raid-clear requirements | Hunt wins |
| Expedition Board Raid-clear requirement | Hunt wins |
| Crystal Guild Airship Raid-clear requirement | Hunt wins |
| Airship upgrade track Raid-clear requirements | Hunt wins |
| Raid Preparedness Guild objective | Renamed **Battle Preparedness**; ordinary combat victories |
| Crystal Resonance Survey Airship mission Raid win input | Hunt wins + Expeditions |
| Relic Recovery Airship mission Raid participation input | Hunt wins + Expeditions |
| Stand Together Weekly Order Raid participation | Expeditions |
| Giant Killers permanent Deed Raid clears | Renamed **Frontier Veterans**; Expeditions |
| Raid Vanguard Legacy milestone | Renamed **Battle Vanguard**; ordinary monster victories |

Existing Gil, item/material, Fellowship-level, and other non-live requirements are unchanged unless listed above.

## Existing-progress protection

The Fellowship system contains a compatibility migration for projects that were already in progress before this hotfix. Existing progress stored under a former `activity:raid_clear` requirement is copied to its replacement offline requirement and capped to the current target. The old row is retained as harmless history.

This means an in-progress Guild Hall, Airship Dock, Expedition Board, Airship construction, or Airship upgrade project does not lose its earned activity progress when the requirement changes.

No database schema change is required.

## Player Guide

`Web/frontend/public/guide-body.html` now explicitly states that Guild construction and upgrade paths are offline-capable and that Raids are optional for infrastructure progression.

If you merge the Web source manually, rebuild the frontend before deployment:

```bash
cd Web/frontend
npm ci
npm run build
```

The separate FULL_DEPLOY_ROOT Web package includes the existing Dockerfile at archive root; its Docker build performs the frontend build automatically.

## Validation

Focused changed-path suite:

- `tests/test_offline_progression_1948.py`
- `tests/test_fellowship.py`
- `tests/test_guild_expansion_beta1.py`

Result: **17 passed**.

A broader Fellowship/Guild/Expedition/Seasonal suite produced **103 passing tests and 3 pre-existing historical assertions** that are stale against the current project baseline (old schema/version/reward-side-effect expectations). No new live-only progression gate was found in the current project definitions.

Player Guide structural/Fellowship checks passed except for one known historical cache-bust assertion that still expects an obsolete v1.8.2 asset revision.

## Install

For a normal full-project merge, extract `CrystalGuild_Offline_Progression_Hotfix_MERGE.zip` over the Crystal Guild project root. It contains `Bot/...` and `Web/...` paths.

Back up the live database before deployment as normal. Restart the Bot after merging so the existing-progress compatibility migration can run.
