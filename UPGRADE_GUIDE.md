# Upgrade to Crystal Guild v1.9.0 Alpha 12 — Camp & Recovery

Starting baseline: complete matching Alpha 11 Mobile Combat HUD (`1.9.0-mobile-combat-hud-alpha11`). This Alpha 12 archive includes all source trees and public assets; you need nothing else to assemble them.

1. Back up local Bot SQLite, hosted Web SQLite and secrets outside the application tree. Test with a copy first.
2. Extract once. Deploy matching `Bot/` and `Web/` source simultaneously. Bot schema 23→24 automatically creates a verified backup before migration; hosted sync stays **1**; action protocol increases to **38** on both sides.
3. From `Web/frontend/`, run `npm ci` then `npm run build` with the pinned lockfile. Assets are already in `public/` inside this complete archive. Do not reuse any earlier `dist` bundle.
4. Reuse your own existing environment files and mounted player database; never overwrite with a test DB. Stage-test the Camp UI, meal timer, two rations from the crafting recipe, free preparation switching, actual Solo Venture buffs and old mobile combat controls. Promote together after smoke testing.

Changes: Trail Rations +10% Solo damage (45-minute departure window), scout +10% Solo XP/JP, gear check +8% Solo damage, supplies 10% post-victory HP/resources, and direct existing Potion/Tent and timed Camp. No durability economy and no effects on other modes.

Rollback: take the Bot and Web releases back to Alpha 11 **with the pre-migration local schema 23 backup**. Do not boot an older Bot against a schema-24 DB.
