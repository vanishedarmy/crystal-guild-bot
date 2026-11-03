# Crystal Guild v2.0.1 — Encounter Balance Audit

## Raid boss profiles

The party-aware HP formulas of v2.0.0 remain, with an armor offset; percentages below are outgoing damage multipliers, armor mitigation at full HP, and raidwide damage multipliers. Enrage is round-based. Scripted Trials have separate existing mechanics.

| Boss | Lv | Tier | HP (4 heroes) | Attack | AoE | Armor | AoE every | Enrage | Signature debuff |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| Goblin King | 6 | World Boss | 5,300 | 0.92x | 0.86x | 2% | 4 | 10 | Weaken |
| Hornet Empress | 10 | World Boss | 6,850 | 0.94x | 0.91x | 2% | 3 | 10 | Slow |
| Skeleton Warlord | 14 | World Boss | 8,050 | 1.03x | 0.88x | 7% | 4 | 11 | Weaken |
| Gigas Chief | 18 | World Boss | 9,400 | 1.11x | 0.78x | 9% | 4 | 11 | Vulnerable |
| Bomb King | 20 | World Boss | 9,000 | 0.99x | 1.14x | 2% | 3 | 11 | Vulnerable |
| Ifrit | 25 | Primal Boss | 16,950 | 1.06x | 1.10x | 4% | 3 | 14 | Scripted Trial |
| Shiva | 25 | Primal Boss | 16,300 | 0.97x | 0.98x | 10% | 3 | 14 | Scripted Trial |
| Ramuh | 28 | Primal Boss | 18,250 | 1.02x | 1.11x | 6% | 3 | 14 | Scripted Trial |
| Ultros | 28 | World Boss | 13,350 | 0.91x | 0.94x | 5% | 4 | 12 | Weaken |
| Garuda | 30 | Primal Boss | 19,500 | 0.99x | 0.94x | 4% | 3 | 14 | Scripted Trial |
| Titan | 32 | Primal Boss | 19,300 | 1.08x | 0.88x | 13% | 4 | 14 | Scripted Trial |
| Demon Wall | 35 | World Boss | 15,000 | 1.00x | 0.92x | 14% | 4 | 12 | Slow |
| Leviathan | 35 | Primal Boss | 21,500 | 1.02x | 1.02x | 8% | 3 | 14 | Scripted Trial |
| Gilgamesh | 45 | High Boss | 28,900 | 1.10x | 0.89x | 8% | 3 | 15 | Weaken |
| Cerberus | 48 | High Boss | 30,300 | 1.09x | 0.89x | 9% | 3 | 15 | Vulnerable |
| Tonberry King | 50 | High Boss | 27,400 | 1.22x | 0.70x | 5% | 4 | 15 | Slow |
| Deathgaze | 52 | High Boss | 32,950 | 1.05x | 0.96x | 7% | 3 | 15 | Weaken |
| Atomos | 55 | High Boss | 33,400 | 0.95x | 1.10x | 12% | 3 | 15 | Slow |
| King Behemoth | 55 | High Boss | 35,800 | 1.14x | 0.91x | 9% | 3 | 15 | Vulnerable |
| Bahamut | 65 | High Boss | 43,150 | 1.11x | 1.12x | 10% | 3 | 16 | Scripted Trial |
| Death Machine Prime | 65 | High Boss | 39,300 | 1.08x | 1.02x | 14% | 3 | 15 | Slow |
| Ultima Weapon | 70 | High Boss | 45,450 | 1.10x | 1.08x | 12% | 3 | 16 | Vulnerable |
| Rift Dragon | 72 | High Boss | 47,100 | 1.09x | 1.02x | 8% | 3 | 15 | Weaken |
| Warmech | 75 | Superboss | 52,750 | 1.09x | 1.05x | 15% | 3 | 17 | Vulnerable |
| Omega | 80 | Superboss | 57,900 | 1.11x | 1.12x | 14% | 3 | 17 | Slow |
| Shinryu | 82 | Superboss | 64,050 | 1.16x | 1.11x | 8% | 3 | 17 | Vulnerable |
| Omega Weapon | 88 | Superboss | 66,900 | 1.12x | 1.15x | 16% | 3 | 17 | Weaken |
| Emerald Weapon | 90 | Superboss | 63,100 | 1.02x | 1.10x | 17% | 3 | 17 | Slow |
| Ruby Weapon | 90 | Superboss | 67,850 | 1.15x | 1.00x | 12% | 4 | 17 | Vulnerable |
| Ozma | 92 | Superboss | 72,200 | 1.02x | 1.16x | 11% | 3 | 17 | Weaken |
| Nemesis | 94 | Superboss | 75,100 | 1.11x | 1.06x | 13% | 3 | 17 | Slow |
| Kaiser Dragon | 95 | Superboss | 76,600 | 1.17x | 1.08x | 14% | 3 | 17 | Vulnerable |
| Long Gui | 96 | Superboss | 77,650 | 1.09x | 0.96x | 20% | 4 | 18 | Slow |
| Proto-Babil | 96 | Superboss | 74,950 | 1.10x | 1.10x | 16% | 3 | 17 | Weaken |
| Penance | 98 | Ultimate Superboss | 83,200 | 1.12x | 1.11x | 18% | 3 | 19 | Vulnerable |
| Absolute Virtue | 99 | Ultimate Superboss | 95,550 | 1.10x | 1.12x | 20% | 3 | 19 | Weaken |
| Yiazmat | 99 | Ultimate Superboss | 89,050 | 1.13x | 1.05x | 18% | 4 | 19 | Slow |
| Eclipse Sovereign | 99 | Ultimate Superboss | 106,200 | 1.18x | 1.15x | 21% | 3 | 20 | Vulnerable |

## World Event profiles

Event ability chance multiplies the base monster signature skill chance before the existing AI profile bias and cap. Attack pressure multiplies damage; physical/magic armor modify the already-scaled event monster DEF/SPR.

| Event | Threat | Attack | Ability frequency | Ability power | Phys. DEF | Mag. SPR |
|---|---|---:|---:|---:|---:|---:|
| Notorious Behemoth | Extreme | 1.10x | 1.24x | 1.08x | 1.05x | 1.00x |
| Tainted Malboro | Severe | 0.92x | 1.38x | 0.83x | 0.98x | 1.08x |
| Dark Iron Giant | Extreme | 1.16x | 1.13x | 1.08x | 1.14x | 0.95x |
| Elder Adamantoise | Severe | 0.88x | 1.16x | 0.93x | 1.25x | 1.12x |
| Cursed Tonberry King | Extreme | 1.22x | 1.22x | 1.16x | 1.02x | 1.00x |
| Savage Coeurl | Dangerous | 1.02x | 1.33x | 0.94x | 0.95x | 0.96x |
| Dread Bomb King | Severe | 0.99x | 1.18x | 1.12x | 0.96x | 0.94x |
| Twisted Ahriman | Severe | 0.94x | 1.32x | 0.93x | 0.96x | 1.15x |
| Ravenous Dragon | Extreme | 1.15x | 1.25x | 1.08x | 1.08x | 1.05x |
| Bloodied Deathclaw | Severe | 1.14x | 1.24x | 1.11x | 1.02x | 1.00x |
| Frostveil Tempest | Elite | 1.07x | 1.30x | 1.02x | 1.06x | 1.13x |
| Mirage Sovereign | Elite | 1.06x | 1.32x | 1.03x | 1.02x | 1.17x |
| Singularity Cataclysm | Apex | 1.14x | 1.33x | 1.07x | 1.13x | 1.13x |

## Targeted standard monster stat corrections

| Monster ID | Adjusted stats |
|---|---|
| elder_ochu | attack 61 |
| inferno_drake | attack 102 |
| malboro_sovereign | attack 132 |
| frost_behemoth | attack 177 |
| tempest_roc | hp 2,175, attack 167, defense 93, spirit 86 |
| aetherstorm_colossus | hp 2,800, attack 161, defense 104, spirit 101 |
| dominion_sentinel | hp 3,550, attack 193, defense 118, spirit 123 |
| emberglass_wyrm | attack 314 |
| frostveil_astrolabe | attack 380 |
| mirage_pharaoh | attack 460 |

## Design and QA notes

- Existing raid loot, event rewards, skill IDs, monster IDs, live-only event rules, HP per-rally freeze, and level gates are preserved.
- Signature raid debuffs occur during generic non-scripted raidwide responses. They last through the next player action; do not add hard CC.
- Scripted Primal/Bahamut mechanics are intact; enhanced boss attack multipliers do not increase their raw scripted damage above V2.0.0.
- Defensive bosses shed some damage mitigation at low HP. HP budgets are partially discounted by initial armor to avoid damage sponges.
- World Event power rises mildly after R12 (normal) / R16 (elite), up to 30%; this is a soft enrage without a forced timer/wipe.
- Validated in deterministic isolated tests, NOT with live Twitch event/raid telemetry or a production deployment.
