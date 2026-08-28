# Validation Report — Crystal Guild v1.2.0 Expeditions Alpha 4

## Automated suites
- Bot: **430 / 430 PASS**
- Hosted Web/API: **47 / 47 PASS**
- Frontend Node regression suite: **305 / 305 PASS**
- Python compilation checks for changed Bot modules: **PASS**

## Alpha 4 coverage
- 20 exploration-derived permanent landmarks
- Atlas landmark totals
- region-specific normal event copy
- rare regional event resolution and persistent Journal history
- Safe / Unknown / Push Deeper rare-event odds
- Push Deeper rare-monster weighting
- compact Adventure payload remains under the established 16 KB guardrail
- Alpha 2 regional milestones/Boss Contracts and Alpha 3 Atlas/Legendary Contracts remain covered

## Compatibility
Local DB schema **8**, hosted sync schema **1**, and Portal Action protocol **20** are unchanged. No player reset is required.

## Production bundle note
The source package does not include `node_modules`, so a local Vite production bundle was not executed. The complete source-level frontend regression suite is passing.
