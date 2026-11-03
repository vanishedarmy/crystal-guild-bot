> Historical V2.0.0 initial HP pass. V2.0.1 further tunes offense, armor, combat pacing and special abilities; see `ENCOUNTER_BALANCE_V201.md`.

# Crystal Guild V2.0.0 — Monster, Raid and World Event Balance Pass

**Status:** Source-level tuning against the existing V2.0.0 Item Reclassification baseline. Version identity remains V2.0.0; no Web rebuild or database migration.

## Scope
- Audited **126 monsters**, **38 raid bosses** and **13 named World Events**.
- Tuned Raid HP at combat start using actual eligible players, boss level, tier, and selected boss-specific identity modifiers.
- Tuned boss single-target attack frequency to match roster size; existing scripted Primal/Bahamut mechanics and scheduled raid-wide attacks are preserved.
- Shifted enrage thresholds to 10/13/14/16/18 rounds (World/Primal/High/Super/Ultimate). Enrage still escalates by 18% per further round.
- Corrected Raid boss Stun chains: boss-targeted Stun proc is 35% of the original chance, lasts one response, then has one protected follow-up round.
- Tuned World Event combat HP using level, tier, threat and joined heroes (not ordinary Venture scaling). This is frozen at combat start.
- Rewards, equipment, raids scripts, monster base attack/defense, World Event eligibility, spawn timing, live-only restrictions, and schema 30 are unchanged.
- Standard monsters are unchanged. Individual unusual enemies remain authored encounters; no blanket stat normalization was applied.

## Balancing assumptions and limits
- **Targets, not measured live outcomes:** Tier budgets target approximately 8–16 raid damage rounds before overshoots from healing, guarding, actions spent on mechanics, limit breaks or rare equipment. Raid sizes from 1 to 20 scale with diminishing returns so additional participants remain valuable.
- Raid HP is calculated once after the rally; it never re-scales after a KO, late action, or revive. A solo participant receives at least a two-hero HP budget to keep raids social.
- World Events remain active **only during live streams**, spawn up to 10 levels above the highest Guild member, and elite variants retain their Lv80/Lv85/Lv95 eligibility gates.
- Raids still show authored *catalog* HP on the Raid Board; the combat-start notice and overlay report the adjusted HP. Those catalog HP values are not the new live-fight HP.

## Raid HP — before vs four-hero combat budget

| Raid boss | Lv | Catalog HP | 4-player HP | 8-player HP | Enrage |
|---|---:|---:|---:|---:|---:|
| Goblin King | 6 | 1,800 | 5,400 | 10,350 | R10 |
| Hornet Empress | 10 | 3,000 | 6,900 | 13,300 | R10 |
| Skeleton Warlord | 14 | 4,600 | 8,450 | 16,200 | R10 |
| Gigas Chief | 18 | 6,500 | 10,000 | 19,150 | R10 |
| Bomb King | 20 | 9,000 | 9,150 | 17,550 | R10 |
| Ifrit | 25 | 18,000 | 17,400 | 33,400 | R13 |
| Shiva | 25 | 18,000 | 17,400 | 33,400 | R13 |
| Ramuh | 28 | 20,000 | 19,000 | 36,450 | R13 |
| Ultros | 28 | 19,000 | 13,800 | 26,500 | R10 |
| Garuda | 30 | 22,000 | 20,050 | 38,450 | R13 |
| Titan | 32 | 26,000 | 21,100 | 40,450 | R13 |
| Demon Wall | 35 | 30,000 | 16,500 | 31,650 | R10 |
| Leviathan | 35 | 29,000 | 22,650 | 43,500 | R13 |
| Gilgamesh | 45 | 45,000 | 30,500 | 58,450 | R14 |
| Cerberus | 48 | 48,000 | 32,200 | 61,800 | R14 |
| Tonberry King | 50 | 18,000 | 28,350 | 54,400 | R14 |
| Deathgaze | 52 | 56,000 | 34,500 | 66,200 | R14 |
| Atomos | 55 | 62,000 | 36,200 | 69,500 | R14 |
| King Behemoth | 55 | 22,000 | 38,050 | 72,950 | R14 |
| Bahamut | 65 | 95,000 | 46,150 | 88,550 | R14 |
| Death Machine Prime | 65 | 30,000 | 43,200 | 82,900 | R14 |
| Ultima Weapon | 70 | 125,000 | 49,300 | 94,600 | R14 |
| Rift Dragon | 72 | 42,000 | 49,650 | 95,250 | R14 |
| Warmech | 75 | 150,000 | 58,450 | 112,100 | R16 |
| Omega | 80 | 190,000 | 63,700 | 122,250 | R16 |
| Shinryu | 82 | 210,000 | 67,600 | 129,650 | R16 |
| Omega Weapon | 88 | 280,000 | 74,650 | 143,250 | R16 |
| Emerald Weapon | 90 | 320,000 | 70,950 | 136,150 | R16 |
| Ruby Weapon | 90 | 340,000 | 73,600 | 141,200 | R16 |
| Ozma | 92 | 375,000 | 77,750 | 149,200 | R16 |
| Nemesis | 94 | 430,000 | 82,050 | 157,450 | R16 |
| Kaiser Dragon | 95 | 475,000 | 84,250 | 161,600 | R16 |
| Long Gui | 96 | 560,000 | 89,250 | 171,200 | R16 |
| Proto-Babil | 96 | 520,000 | 83,650 | 160,500 | R16 |
| Penance | 98 | 700,000 | 94,200 | 180,750 | R18 |
| Absolute Virtue | 99 | 1,000,000 | 109,850 | 210,750 | R18 |
| Yiazmat | 99 | 850,000 | 100,850 | 193,450 | R18 |
| Eclipse Sovereign | 99 | 1,350,000 | 122,950 | 235,900 | R18 |

**Why the largest changes?** The original catalog ranges from 1,800 to 1,350,000 static HP even though the same raid engine handles a solo participant and a large Twitch roster. An ultimate boss is now harder primarily because of raid mechanics, pressure and late enrage; not because a four-person party must grind through a million HP.

## World Events — four-player illustration at highest Guild character Lv99

These examples use the median level bonus for each event, not a promise of a particular spawn level. The old HP is the previous ordinary party multiplier applied to the scaled World Event template.

| World event | Sample enemy Lv | Previous HP | Balanced HP |
|---|---:|---:|---:|
| Notorious Behemoth | 107 | 22,282 | 22,323 |
| Tainted Malboro | 106 | 16,834 | 19,766 |
| Dark Iron Giant | 107 | 20,769 | 22,323 |
| Elder Adamantoise | 105 | 40,112 | 19,600 |
| Cursed Tonberry King | 107 | 23,970 | 22,323 |
| Savage Coeurl | 104 | 13,425 | 17,491 |
| Dread Bomb King | 105 | 16,539 | 19,600 |
| Twisted Ahriman | 106 | 14,520 | 19,766 |
| Ravenous Dragon | 107 | 30,837 | 22,323 |
| Bloodied Deathclaw | 106 | 21,499 | 19,766 |
| Frostveil Tempest | 107 | 89,355 | 33,485 |
| Mirage Sovereign | 107 | 100,912 | 33,485 |
| Singularity Cataclysm | 108 | 137,031 | 37,983 |

World Events retain their higher XP/JP/Gil and elite loot rules. Changed HP is not a reward multiplier.

## Standard monster catalog findings
- All 126 monster IDs remain present with their original HP/attack/defense/spirit/rewards and unique enemy action mapping.
- `cactuar` has intentionally low HP compared with nearby Lv10 mobs; normalize-by-level would destroy its distinct behavior.
- `tempest_roc` (Lv32) and `emberglass_wyrm` (Lv62) are stronger than ordinary nearby enemies; retained as exceptional monsters, not forced to the median.
- `eclipse_harbinger` (Lv100) and `singularity_archon` (Lv103) exceed the Lv99 character cap; retained as endgame threats and World Event source templates rather than silently clamping their levels.

## Tests and confidence
- Passed: 6 new balance tests, 10 live World Event tests, 41 raid script alpha tests, 92 engine tests, 13 base-balance tests, 7 world-event-exclusivity tests, 10 raid healing tests, 5 limit-break tests, 9 consumable tests, 24 Active Battle tests, 19 Active Hunt tests, and 25 Beastmaster tests (**261 selected tests total**).
- Broader legacy historical tests include pre-existing version/schema/region-count assertions incompatible with the already-released V2.0.0 baseline (e.g., expect v1.9.9 or DB schema 27 instead of 30). The unrestricted full-suite run exceeded its time limit. **This is not a full production QA pass.**
- No deployed Twitch stream, live player roster, or live combat telemetry was tested. Actual fight duration and wipe rates need observation to refine target rounds.

## Installation
1. Back up the existing V2.0.0 Bot source and live SQLite DB.
2. Choose **one**: merge the small Bot patch into the installed Bot, or replace Bot application source using the complete Bot archive.
3. Preserve the live database, `.env`, secrets, deployment scripts/settings, and existing Web source; no Web files change.
4. Restart the Bot. Existing active rallies/raids should finish before upgrading to avoid changed HP during a resumed fight.
5. Verify raid spawn → join → start (party-scaled HP), and a live-only World Event → join → start.

**Source files changed:** `Bot/crystal_guild/engine.py`, `Bot/data/bosses.json`; new helper `Bot/crystal_guild/encounter_balance.py`; new tests `Bot/tests/test_enemy_balance_v200.py`.
