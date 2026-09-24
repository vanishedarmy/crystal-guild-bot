# Crystal Guild v1.9.0 Alpha 12 — Camp & Recovery

The complete Alpha 12 release builds on Alpha 11 Mobile Combat HUD and includes the matching Bot source, hosted Web source, and **all public assets already assembled at `Web/frontend/public/`**. Extract the one ZIP once.

## Three deliberately small Camp choices

- **Eat a meal:** Trail Rations are available in the shop for 95 Gil and craftable in batches of two from Fish Scale ×1, Potion ×1 and 20 Gil. Eat one at the Adventure Board Camp to gain **+10% damage throughout the next Solo Venture**, provided you depart within **45 minutes**. Eating uses one ration once, prevents accidental double-consumption, and lasts all three stages once the run begins.
- **Recover:** Preserve the existing free timed Camp. The new Camp panel also offers one-click use of a carried **Potion** or **Tent** through the original server-owned field-item rules. No gear degradation or repair economy is introduced.
- **Choose one free preparation:** **Scout the Route** grants **+10% secured stage XP and JP**; **Check Your Gear** grants **+8% damage** for the entire Solo Venture; **Pack Supplies** restores **10% HP and MP/AP** after each defeated Solo Venture enemy. Switch plans freely before departure; the choice is consumed only when a Solo Venture actually starts.

Meals and choices persist safely in the local SQLite database until a run begins or the meal expires. Their bonuses are intentionally limited to **Portal Solo Ventures**; Hunts, Rally Ventures, Dungeons, Raids and other combat modes keep their existing behavior.

## Compatibility and safety

- Bot and hosted Web release `1.9.0-camp-recovery-alpha12`. Local Bot DB schema **24** (verified pre-migration backup from schema 23), hosted sync schema **1**, Portal Action protocol **38**. Both services must be upgraded together.
- The original Alpha 11 mobile combat HUD and losslessly optimized Trading Post WebP artwork are carried forward; the public assets are supplied in their proper folder.
- Authoritative Bot actions, idempotency receipts and strict hosted-action shape checks prevent duplicate meals and arbitrary client-provided bonuses. The Adventure Board projection stays within its existing compact response budget.
- Preserve the existing live Bot SQLite database, mounted data volumes, hosted Web store, OAuth/session credentials and environment variables. Test migration on a backup before live deployment. **Do not deploy only one half of the protocol upgrade.**

## Build status

This is a **complete source handoff**, not a live deployment or prebuilt Vite bundle. From `Web/frontend`, install pinned dependencies with `npm ci` and create fresh assets with `npm run build` on the target build machine, then do a responsive browser walkthrough of Camp and the retained mobile combat HUD.

The new Camp-specific unit tests are in `Bot/tests/test_camp_alpha12.py`.
