# Crystal Guild v1.5.0 — Trails & Raids

Stable production promotion from the validated RC1 baseline. The seven scripted Trials, Trial Chronicle, repeat mastery, exactly-once settlement, authoritative round state, readiness hardening, and the four v1.4 Dungeons are unchanged from RC1.

## Production visual additions
- Active timed Hunts now use `/trails-raids/hunt-active.webp`.
- The collapsed Trial & Raid Board uses `/trails-raids/trial-board-collapsed.webp`.
- The open Trial & Raid Board uses `/trails-raids/trial-board-open.webp`.
- All three generated PNG sources were converted to shipping WebP assets; no PNG is added to the Web package.

## Compatibility
- Runtime: `1.5.0-trails-raids`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- No database migration, player reset, OAuth/environment change, or new environment variable.
