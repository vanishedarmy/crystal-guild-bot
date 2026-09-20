# Crystal Guild v1.8.2 — Fellowship Project Selection Hotfix Validation

## Result

**PASS** for the Fellowship selection repair.

## Validation

- Frontend unit/regression suite: **696 / 696 passed**.
- Fellowship / Portal-action / live-stream-control / Merc-help Bot regression set: **77 / 77 passed**.
- Fellowship-specific Bot tests: **10 / 10 passed**.
- Python `compileall` for the Bot package: **passed**.
- Manual isolated reproduction confirmed that `Moogle Emporium Annex`, `Annex`, `Guild Archive`, and `Chocobo Stables` resolve to their currently available construction projects.
- Ambiguous `Guild` remains rejected.

## Full Bot-suite note

The complete Bot suite was started in this environment, but its long-running process exceeded the execution window before returning a final summary. The changed Fellowship/Portal paths and adjacent regression set above completed cleanly.

## Scope

No construction costs, unlock requirements, rewards, schema, hosted-sync version, or Portal Action protocol were changed.
