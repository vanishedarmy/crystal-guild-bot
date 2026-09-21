# Crystal Guild v1.9.0 Alpha 6 — World Events Validation

Validation target: runtime/frontend `1.9.0-world-events-alpha6`, local schema **19**, hosted sync schema **1**, Portal Action protocol **36**.

## Automated results
- Bot full regression suite: **782 / 782 passed**.
- Focused Bot World Events suite: **10 / 10 passed**.
- Hosted/Web Python suite: **80 / 80 passed**.
- Focused Alpha 6 frontend World Events checks: **5 / 5 passed**.
- Full frontend history suite: **659 / 716 passed**. The remaining **57** failures are exactly the same inherited historical release-name and legacy PNG-policy assertions as the Alpha 5 baseline (**654 / 711**, also 57 failures). Alpha 6 adds five passing frontend tests and introduces **zero new full-suite failure names**.
- Python source compilation: **passed** for Bot and Web packages.
- Game-data reference/range/balance validation: **0 errors**.

## World Event coverage
- Stream-only spawning is enforced and a World Event cannot overlap another Guild-wide encounter or Raid.
- The autonomous scheduler runs from the combat director with a 15-minute opening grace period, 8–12 minute eligible scan interval, 25% roll, and 30–45 minute post-event cooldown.
- All ten initial World Event definitions have distinct IDs, stable art routes, valid familiar base monsters, threat identities, and controlled +3 to +10 scaling bands.
- The hard ceiling is the Guild's highest current character level **+10**. A level-99 Guild can therefore legitimately see a level-100–109 World Event.
- World Events use the existing Active Battle engine and **never create a Raid**.
- An unanswered 90-second World Event rally closes cleanly and enters the normal event cooldown.
- World Event participation does not consume the normal Venture cooldown or increment the player's Venture count.
- Hosted Portal `LIVE_EVENT_JOIN` and `LIVE_EVENT_ACTION` validation accepts the `world_event` event kind end-to-end.
- Twitch `!encounter`, battle-history labels, Portal live-state presentation, and participant result messaging use the enhanced variant identity safely.
- Adventure State preserves the existing **16 KiB safety ceiling** by sending only authoritative live World Event state; the static 10-boss display catalog ships with the matching frontend build.

## Portal and artwork
- Stream Activities contains a dedicated World Events area separate from Raids.
- Ten individual World Event boss portraits and four supporting state/header assets are packaged under `/world-events/a1/` as WebP.
- Responsive roster behavior scales from wide desktop to a single-column narrow-mobile layout.
- Active, idle, and defeated state artwork is wired into the World Events presentation.

## Compatibility
No database migration, hosted sync bump, Portal Action protocol bump, player reset, economy rebalance, Gold Saucer payout change, or Title requirement change is required.

## Frontend build-environment note
The source snapshot does not include installed frontend `node_modules`, so a production Vite bundle was not rebuilt inside this isolated workspace. The Node source-contract/history suites ran directly and all new Alpha 6 checks pass. Normal deployment remains responsible for installing the pinned package dependencies before the Vite production build.
