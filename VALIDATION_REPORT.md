# Validation Report — Crystal Guild v1.2.0 Expeditions Alpha 5

## Automated suites
- Bot: **434 / 434 PASS**
- Hosted Web/API: **47 / 47 PASS**
- Frontend Node regression suite: **306 / 306 PASS**
- Python compilation checks for changed Bot/Web modules: **PASS**

## Alpha 5 coverage
- Chocobo specialty derives from the five existing traits.
- Bond tiers scale at Chocobo levels 1 / 5 / 10 / 15 / 20.
- Pathfinder travel scaling, Forager material scaling, Guardian/Treasure rescue scaling, and the 90% rescue cap are covered.
- Completed Expedition Hunt Seal stipends are covered for normal, Regional Boss, and Legendary depths.
- Defeat does not award a completion stipend.
- Expedition accomplishment counters are exposed through the Chocobo Stable state.
- Adventure Board specialty data remains compact and the full Adventure payload remains below the established 16 KB guardrail.
- Alpha 2 regional progression, Alpha 3 Atlas/Legendary Contracts, and Alpha 4 Regional Discovery/Journal regressions remain covered.

## Patch validation
A4 → A5 Bot and Web patches are verified by applying each patch to a clean Alpha 4 tree and comparing the reproduced tree against the final Alpha 5 package. Runtime/secret hygiene exclusions are applied to release archives.

## Compatibility
Local DB schema **8**, hosted sync schema **1**, and Portal Action protocol **20** are unchanged. No migration or player reset is required.

## Production bundle note
The source package intentionally does not include `node_modules`; the local Vite executable is therefore unavailable in this release environment and a Vite production bundle was not executed. The complete source-level frontend regression suite and JSX/source parsing coverage are passing.
