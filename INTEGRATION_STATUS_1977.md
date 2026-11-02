# Crystal Guild v1.9.97.7 — REAL BOT Item & Relic Integration Candidate

## Provenance
- Input: user uploaded `Bot(1).zip`, version `1.9.97.7-regional-progression`.
- This is an updated copy of the actual Python Bot, NOT a standalone JavaScript staging simulator.
- Web source, production database and deployment were **not** altered.

## Live Python Bot paths updated
- `data/items.json`: 618 same item IDs, applying the consolidated staged rarity/level/stat/special effects catalog, including 108 stage metadata records and 54 Ultimate signatures.
- `crystal_guild/data.py`: accepts Unique/Exotic and forbids Relic rarity on non-Relic weapons.
- `crystal_guild/engine.py`: reads actual database equipment, enforces level/job restrictions before applying special gear properties, combines partial status resistances multiplicatively with an 80% cap, retains full status immunity, and injects verified item/Relic properties into encounter and raid snapshots.
- `crystal_guild/relic_live.py`: bounded Python helpers for matching Relic perks to weapon, job, action, enemy and equipment.
- Activated action hooks include conditional Dragoon Jump/Dragonfall, Warrior Guard-to-Strike, White Mage healing/Lifewave, Red Mage hybrid ability bonuses, Dark Knight vulnerable damage and dark-attack healing, elemental critical Black Mage abilities, Samurai Iaijutsu critical bonuses, Summoner/Sage MP/AP discounts, Bard song buff duration/potency, Ninja evade protection, Machinist active ranged accuracy/critical damage, selected Beastmaster abilities, Blue Mage combat spell damage, Time Mage slow resistance/damage, and selected early-stage themed accessories.
- Weapon on-hit status and lifesteal now have a limited **basic-weapon-only** Raid path. Boss stun is intentionally disallowed; raid proc chance is reduced.
- Special gear hooks added for Dragon Slayer vs verified dragon-family enemies, Dragoon Boots Jump, Sage's Emblem costs, Grudge Lantern kill healing, Behemoth Crown direct-hit mitigation, Sniper Eye and Machinist's Goggles.

## Known incomplete / not claimed live
- Some Relic traits remain metadata-only because the Python Bot lacks the required action receipts or dedicated gameplay hooks: Thief Steal success, Monk three-hit combo AP returns, Paladin Cover protection/counter, Red Mage Spell Echo, Blue Mage learning chance, Beastmaster-owned-pet attack pipeline, and Artisan's Hammer crafting bonus.
- Several perk conditions are live only in Active Battles, not raids (e.g. Black Mage critical spells, Samurai Iaijutsu crit, low-HP Warrior protection, Dark Knight HP drain).
- Ultimate weapon stat progression was deliberately not additionally inflated beyond the staged rework. Stage buffs and perk descriptions should be reviewed in live encounters.
- The JavaScript V2.6 SQLite transaction reference was **not** dropped into this Python Bot. Existing Bot DB/engines remain authoritative. No new migrations or production transaction semantics claimed.
- The Web/Item Encyclopedia compatibility patch must still be merged and tested separately.

## Validation
- New integration and focused regression tests: 80 passed, with 41 additional subtests.
- Broader focused combat suite: 56 passed, 1 failed. The failure was reproduced *unchanged on the uploaded baseline*: an outdated expected Ultimate quest error message.
- Two old Arsenal II tests also fail unchanged on the uploaded baseline because the current Job ability catalogs have more abilities than their obsolete assertions expect.
- A complete project suite did not finish within the execution limit, so full-suite parity is NOT claimed.
- Unit and syntax validation passed; no live Twitch/Portal/production DB test was possible.

## Deployment
1. Back up existing Bot directory and player SQLite database / production DB.
2. Verify actual live Bot version is 1.9.97.7 before replacing files.
3. Either use the complete Bot ZIP (merge `Bot/`) or the small delta ZIP (merge exact tree). Never deploy both.
4. Review test logs and QA in this report; run on a staging database.
5. Validate player gear gating, Ribbon immunity, Hunts/Ventures, Raids, World Events, MP/AP and relic quest rewards before production.

If a true complete production-ready 18-job perk rollout is required, the remaining specialized mechanics need additional work and user acceptance tests; this candidate is deliberately labeled partial.
