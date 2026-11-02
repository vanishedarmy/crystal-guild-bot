# Crystal Guild v1.9.97.7 — Bot Integration V2.7 (Source Candidate)

## Inputs and scope
- Based on the actual uploaded Python Bot v1.9.97.7 and the prior approved item/Relic integration candidate.
- Only this working copy was modified; the uploaded original, deployed Bot, and Web build are unchanged.
- Keeps all 618 catalog items and 108 Classic/Ultimate Relic configurations unchanged.

## New live-source hooks in this candidate
1. **Artisan’s Hammer (Portal crafting):** If equipped in the accessory slot and the player meets Lv35, a successful `portal_craft_recipe` rolls a 5% chance to salvage **one** of the recipe's consumed Common/Uncommon/Rare *material* inputs. The roll occurs once per submitted craft action, not per item produced; no equipment or Exotic/Unique/Legendary/Epic material can be duplicated. The returned material, transaction ledger entry, craft output, and Portal action receipt are written inside the same SQLite transaction. A second receipt check inside the write transaction avoids repeat crafting if concurrent workers pass the initial read.
2. **Paladin — Sacred Guard:** Successfully using the existing `Cover` ability on a living other ally arms the Paladin's verified equipped Relic `sacred_guard` modifier. One actual incoming hit on the Paladin consumes the charge for the staged percentage damage reduction (Lv99 Eternal: 30%). A successfully evaded hit does not consume it. It remains encounter-local.
3. **Paladin — Aegis Reprisal:** Surviving the protected direct hit arms a one-time basic attack against the enemy, using the Ultimate Relic signature percentage (Lv99 Eternal: +18%). Missing an attack does not consume the charge; it applies only to a successful subsequent basic attack. This is a **next-basic-attack reprisal**, not an immediate free counterattack.

## Still pending
- These new Paladin hooks cover the shared **Active Battle** enemy-hit path (hunts/ventures/world events using that resolver). Raid enemy hit processing is distinct and has **not** been wired in V2.7.
- Thief Steal success, verified Monk 3-hit-combo AP rewards, Blue Mage learning chance, Beastmaster owned-pet pipeline, and other advanced Relic receipts remain pending. The current Python active ability dataset does not support a verified Steal / 3-hit action / learn event, so no fake passive buffs were added.
- Some other perk hooks and specialized encounters may need server-side action receipt support beyond this pass.
- This is an installable source candidate, **not a deployed live update**; backup Bot and player database before deployment. No production deployment tests have been performed.

## Test results
- 8 new V2.7 tests pass: crafting eligibility, replay safety, material-rarity exclusions, failed-craft safety, transaction rollback, Paladin Cover/guard and Reprisal, and evade handling.
- Extended targeted run: **187 run, 180 pass, 7 fail**. All seven failures reproduced with the untouched baseline Bot and are outdated assertions (crafting recipe counts, old Portal payload limits/regions). No new regressions found in these suites.
- Original Bot and prior integrated candidate remain available for rollback.

## Merging
- Choose the full updated `Bot/` archive **or** the delta archive, not both.
- Maintain the standard folder structure; do not install over an active process. Restart the Bot and smoke-test representative cover, craft, venture and raid actions against a **backup database**.
