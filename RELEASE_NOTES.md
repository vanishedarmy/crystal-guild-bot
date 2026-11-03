# Crystal Guild v2.1.0 — Adventure Tales

The consolidated v2.1.0 release integrates the latest V2.0.1 fixes and expands Expedition/Dungeon storytelling.

- Expedition Tales: all 11 regions have stored, contextual journey narration; combat, rewards and travel odds are unchanged.
- Dungeon Tales & Rest: randomized saved room routes and personal narration across ten dungeons, with a shared 600-second dungeon cooldown after completion, retreat or defeat. Job Ascension Trials remain exempt.
- Guild Board and Fellowship are combined into Guild Town → Guild Board. The redundant top header Guild Board link is removed (desktop and mobile).
- Bestiary uses Item Catalog-style search, filters, result cards and a separate dossier, including undiscovered portrait artwork.
- Includes regional enemy placement, Moogle Emporium stock fixes, Limit Break/Expedition reliability repairs, targeted streamer activity controls, and portal visual/accessibility passes from V2.0.1.
- Version bump only: database schema and Portal Action protocol are unchanged. Player databases and configuration must be preserved.
- Bot and Web need to be deployed together for compatible action validation, content and presentation.

# v2.0.1 — Expedition Tales (additional Bot-only update)

- Add distinct arrival, travel, encounter, camp, event, and return narration across 11 Chocobo/Airship Expedition regions.
- Scenes are stored through existing event labels and Expedition history; reloads retain the same story, and existing in-progress runs remain compatible.
- Narrative selection is isolated from gameplay RNG. No adjustments to timing, cooldown, combat, drops, probabilities, unlocks, databases, or Web interface.

---

# v2.0.1 — Expedition Reliability & Targeted Streamer Recovery (additional update)

- Fix independent Expedition launch being blocked by a global active Guild Raid/encounter belonging to other players; personal conflicting activities and combat rosters remain protected.
- Owner-only targeted recovery through `!removeactivity <username>` and Portal `STREAMER_COMMAND(removeactivity)`, restricted to the verified streamer account. Clears only the selected player's active Expedition, Solo Venture, Dungeon, Hunt, World Event, field combat or Raid membership. Boss battles with no remaining players are retired safely; current progress and inventory remain unchanged, and unbanked rewards are forfeited.
- Persist removal and Portal action idempotency receipt in the guarded transaction; no schema migration.
- Requires matching Web hosted-backend+frontend patch for the Streamer Control Center and Expedition countdown behavior.

---

# V2.0.1 — Dungeon Adventure Variety (additional update)

- Four standard Dungeons (9–10 chambers) and six advanced Ascension Dungeons (8–9 chambers) now snapshot randomized routes on entry, with unique chamber order, dungeon-themed normal opponents, rotating elites, and randomly selected minor events. Dungeon bosses remain the original final enemy.
- Each run's route is persisted in existing Dungeon state JSON and validated against exact room IDs and saved revisions. No migration. Older in-progress runs, rewards and Job-specific Ascension Trials remain unchanged; advanced Ascension Dungeon boss scripts are preserved.
- New random pools exclude monsters reserved for World Events. Room HP variation is mild and rewards continue through the existing systems.
- Accompanying Web patch refreshes the Dungeon Board, Guide and What's New without artwork replacement.

---

# Crystal Guild v2.0.1 — Encounter Rebalance

**Scope:** Combat-tuning release built on the v2.0.0 Item Reclassification + initial V2.0.0 Enemy Balance Bot. No data migration, reward reset, artwork replacement or new command syntax.

- **38 Raid bosses:** Distinct outgoing pressure, defense/armor, AoE cadence, delayed enrages, and party-aware HP. Armor loses some effectiveness below 30% HP, allowing a final push. Max HP is discounted for armor so armored bosses do not become HP sponges.
- **Soft raid mechanics:** 31 unscripted raid bosses may inflict brief Weaken, Slow or Vulnerable on surviving raiders during signature rounds. Hard stun/silence and damaging poison are intentionally excluded. Immunity and resistance from equipment still work. Seven scripted Trial bosses retain their authored mechanics; their scripted base damage is never increased by V2.0.1.
- **Target fairness:** Generic raid boss strikes preferentially spread between living players instead of repeatedly piling all strikes onto one random player; tanks and Taunt still attract attacks.
- **13 live-only World Events:** Individual attack pressure, skill frequency/power, status control intensity, and physical/magic defenses. Party-wide ability bursts are reduced per target in very large groups, and hard-control status infliction is capped. Gentle soft enrage begins after round 12 for normal events and after round 16 for elite events, up to 30% extra pressure.
- **126 regular monster records:** Targeted normalization for 10 unusual stat outliers, including Tempest Roc and Dominion Sentinel, without deleting special skills, drops, reward values, monster identities or Hunt eligibility.
- **Progression:** Item/Relic/Job systems, World Event rewards and live-only eligibility, raid loot, schema 30, and the full existing database remain unchanged.

**Upgrade:** Finish any currently active Raid or World Event, back up Bot source, secrets/config and database, then apply either the full Bot source or the merge patch. Web version/What's New changes are distributed separately as a source-only version/UI merge patch; apply it to the existing Web and rebuild the frontend with your normal deployment workflow. Do not overwrite a persistent database, `.env`, or live configuration.

**Validation:** Automated tests check encounter profile coverage, armor, scripted raid compatibility, behavior copy isolation, controlled status effects, crowd AoE, event frenzy limits and live-only restrictions. No live Twitch roster was simulated; observed clear times, wipes, and player levels will be needed for further tuning.

---

# Crystal Guild v2.0.0 — Item Reclassification

**Release scope:** Unified Bot V2.12 gameplay and synchronized Web V2.13 item/Relic/companion presentation, promoted to public version `2.0.0`. The existing Python Bot and Web source are the release baseline; no database reset is required.

- **618-item catalog:** Restructured progression and item attributes; `Relic` is exclusive to the 108 actual Relic Weapon rewards. `Unique` and `Exotic` are supported in rarity displays and the Player Portal catalog.
- **Level and stat balance:** Ribbon Fragment (Lv35) precedes the stronger Ribbon (Lv55, Exotic). Targeted accessory, weapon, and armor adjustments from the integrated catalog are preserved.
- **Equipment properties:** Elemental alignment, status immunity/resistance, on-hit effects, specialized equipment mechanics, and the gear-effect balance pass remain in the source with eligibility and combat restrictions.
- **Relic Weapon rework:** 54 Classic and 54 Ultimate Relic forms retain their job-specific abilities; Ultimate forms have empowered primary perks and signature abilities. Quest progress and item IDs are preserved.
- **Beastmaster companions:** Persistent tame/roster, active companion, 20 Bond ranks, XP rewards across supported victories, and Portal companion overview. The current Bot database schema remains **30**.
- **Web synchronization:** Item Encyclopedia and Guide reflect the authoritative 618 Bot item records; new classifications and Relic/companion properties are displayed, with approved artwork Batches 01–15 preserved.
- **Version identity:** Bot runtime `2.0.0-item-reclassification`; Web `v2.0.0 — Item Reclassification`; both application package manifests `2.0.0`.

**Upgrade:** Back up persistent player databases, live secrets, and Bot/Web environment configuration. Replace only application source, not the live database. The supplied Web archives are full **source** packages, not a newly compiled production frontend; run `npm ci && npm run build` on the deployment host before publishing new static assets. Browser smoke tests and production deployment are still required.

---

# v1.9.97.7 — Regional Progression

World-map regions unlock at Levels 1, 10, 20, 30, 40, 50, 60, 70, 80, 90, with an optional Level 99 capstone. Existing region IDs are preserved. Newly added Shattered Frontier (Level 60) and Astral Threshold (Level 90) use regional monsters of appropriate strength. Classic Relic Crystal Cores can now be obtained from Crystal Expanse foes around Levels 45–49; Eidolon Shards from Shattered Frontier foes around Levels 62–68. Hunt Seal exchanges remain valid. Existing player states and expedition routes are unchanged.

## v1.9.97.6 — Job-Level Reward Balance

- Job Points scale from the current Job Level rather than Character Level; switching to a new Job no longer inherits a 35%-of-character-level penalty.
- Standard battles, World Events, Solo Ventures, Expeditions and Dungeon enemy payouts use the adjusted shared Job Point multiplier. Repeat Dungeon bonus JP scales by Job Level independently from Character XP and Gil.
- Character XP and Gil keep their existing character-level anti-farming rules. No earned progress, equipment, class unlocks or save data is reset.
- See `RELEASE_NOTES_1976.md` for the exact scope and limitations.

## v1.9.97.4 — Relic Portal Awakening

- Added authenticated Relic stage advancement in Portal Relic Arsenal, with confirmation and full server-side requirements validation.
- Retry-safe atomic stage/receipt transaction; Twitch !awaken remains compatible.
- No player progression or inventory reset.

# Crystal Guild v1.9.97 — Elite Hunts & World Events

- Six high-level Hunt assignments: three S+ (Character Lv.80, 86, 92) and three SS (Lv.95, 99, 99).
- Existing automatic personal Hunt simulation retained. S+ duration 5 hours; SS 6 hours. Lower ranks unchanged.
- Unlock rules use unique clears in prior rank; Hunt first-clears award existing material + new exclusive title. Repeat wins have a chance to award a bonus rare endgame material (30–50% by mark).
- Three new stream-only Elite World Event variants (eligible when highest Guild character reaches 80/85/95); normal variants remain available below that threshold. Shared event schedule and join flow unchanged.
- Elite event victories award an extra guaranteed themed rare item and use a 45% premium drop chance; normal World Events retain their previous 20% premium chance and 4x XP/3x JP/2x Gil calculation.
- Portal Hunt ranks and World Event roster, What's New, and public Player Guide updated. Guild Town and standalone Ascension Trials remain intact.
- Existing player data, titles, trophies, progress, old events and database schema remain unchanged. No original Web art should be deleted.

---

## v1.9.96 — Sovereign Encounters
- Three new six-room high-level Dungeons: Abyssal Foundry (Lv.65), Void Cathedral (Lv.85), Throne of Eternity (Lv.99). The existing Lv.55/75/95 Ascension Dungeons remain fully playable and now include advanced guardians.
- Advanced guardian combat in six Ascension Dungeons and JLv.75/90/99 Job Trials: phase shifts at 60% and 25% HP change elemental weaknesses/resistances and raise enemy pressure. Matching elemental attacks receive a 40% weakness bonus or 35% resistance penalty against these bosses; existing normal monster elemental logic is preserved.
- Telegraph heavy attacks before the acting hero chooses their next turn. Defend provides normal protection plus an additional special guard counter (40% reduced power) for the marked strike. Statuses (including stun) still interact with monster turns.
- Portal combat displays phase name, current elemental weaknesses/resistances and a prominent DEFEND warning. Public Player Guide and What's New now include this release. Existing player saves, Job Trials, Limit Break unlocks, equipment and item fixes remain intact; no SQL schema or protocol migration.
- Validation: dedicated advanced encounter regression suite and focused combat/Portal tests; production frontend compilation and live Twitch/Portal E2E require staging validation.

## v1.9.95 — Trials of Ascension
- 72 Job-specific, persistent guardian trials (18 Jobs × JLv.60/75/90/99) with separate character-level gates, sequential prerequisites, class-themed objectives, combat seals and first-clear rewards.
- 36 new Job titles (JLv.75/99). Persistent Job-specific permanent passives at JLv.60/90/99 are awarded only once and never stack on replay.
- Three six-room endgame Dungeons: Forgotten Crystal Sanctum (Lv.55), Celestial Spire (Lv.75), Astral Crucible (Lv.95), including meaningful route/hazard/sanctuary choices.
- Twitch: `!ascension`, `!jobtrials`, `!ascend <60|75|90|99>`, `!trialaction <attack|defend|ability:id|limit:tier|item:id>`, `!trialretreat`. Portal: new current-Job trials board and live guardian-seal objective progress.
- Updated Guide, What's New and release metadata; retains v1.9.94 fixes and all previous equipment, Job and Limit Break expansions. No DB schema or sync-protocol change. Rebuild and smoke-test Web before deployment.

## v1.9.94 — Battle & Rewards Hotfix
- Audited all 34 consumables' effect definitions and tested full recovery for mixed MP/AP party members in both standard battles and raids. Megalixir sets all conscious allies to maximum HP and applicable MP/AP **at item resolution**; enemy retaliation later that round still causes damage. No unrequested invulnerability or global item rebalance.
- World Event wins now grant 4× XP, 3× JP and 2× Gil relative to their normal scaled victories, plus one guaranteed thematic rare drop and a 20% premium-bonus roll. Existing normal monster drops and seasonal tokens still apply; no rewards on defeat.
- `!revive <player>` now works in active Stream Ventures and World Events as well as Raids. It consumes one Phoenix Down only on successful revival. Solo Expeditions/Dungeons remain single-player and are not ally-revive contexts.
- Mobile combat quick bar prominently displays enemy name, current/max HP, percentage and large HP gauge in all six combat views. What's New and Guide updated.
- No database schema or sync protocol changes. Bot/Web should deploy together.

## v1.9.93 — Limit Break Awakening (18 Jobs · 72 Limit Breaks)

- Every playable Job unlocks four named Limit Break techniques at Job Levels 50, 75, 90 and 99. Job Mastery remains JLv.50, and the v1.9.92 169 active techniques and 90 passive milestones remain available.
- The Limit Gauge builds during battle, displays 0–100% progress, illuminates when ready, and resets when a Limit Break resolves. Queueing or changing an action in a raid does not waste charge.
- Limit Break categories are class-aligned: devastating damage, defensive party cover and counterstrike, party healing with high-tier revival, and party inspiration.
- Commands: `!limit` activates the strongest unlocked technique when charged, or `!limit 50`, `!limit 75`, `!limit 90`, `!limit 99` selects an unlocked tier. The raid overlay shows charge for participating heroes.
- Portal Solo Ventures, Expeditions and Dungeons also display the gauge and offer a dedicated Limit Break button. The Portal Overview What's New now includes detailed entries for **both** Job Ascension (v1.9.92) and Limit Break Awakening (v1.9.93), with expandable release history.
- Battle-scoped charge, no MP/AP spend. Backward-compatible persistence; no player table/schema change.
- Frontend production build and live Twitch/Portal verification are still required before public deployment.

## v1.9.92 — Job Ascension (Character and Job cap: 99)

- All 18 Jobs advance from JLv.50 to JLv.99 while retaining cross-Job Mastery at JLv.50 and the existing Ultimate Relic prerequisites.
- 169 new active abilities across the 18 Jobs, including seven missing Black/White Mage middle-tier spells; 90 new passive milestones. All Jobs gain high-level actions at JLv.52, 58, 64, 70, 76, 82, 88, 94 and 99, plus passives at 55, 65, 75, 85 and 95.
- Black Mage adds Watera, Osmose, Quake, Tornado, Firaga, Blizzaga, Thundaga, Waterga, Firaja, Blizzaja, Thundaja, Meteor and Apocalypse.
- White Mage adds Curaga, Aeroga, Medica, Curaja, Protectra, Shellra, Esunaga, Arise, Holyga, Regenra, Divine Benison and Afflatus Rapture. Cura is the canonical display name for the existing Cure II ID; legacy !ability Cure II targeting continues to work.
- Job JP processing, validation, server/Portal job levels, Guide and Portal ability reference updated. Existing saved Job Level 50 characters continue leveling normally. No database schema migration.
- Uses supported Active Battle effect types and existing resource/damage/heal limits; Arise is a full-HP revive. Includes new progression tests and updated catalog-total expectations.
- Source-only Web distribution requires an ordinary frontend build/deploy. Preserve deployment databases, environment variables, secrets, existing artwork and existing Web public assets.

## v1.9.9 — Skybound Singularity

- Three additional Airship Expedition regions (6 total), each with a regional boss, exploration landmarks, materials and illustrated backdrops.
- All three previously established Airship regions also receive original scenic artwork.
- Eclipsed Singularity Citadel, a separate Lv.97 World Map region beyond Omega Ruins, with new creatures and an Eclipse Sovereign Ultimate Superboss raid.
- Existing expeditions, saves, and Cloud sync protocol remain compatible.

## v1.9.8 — Item Effects Audit Hotfix

- Hardened HP/MP/AP restorative item math across field, standard battle, and Raid/World Event use. Full-effect items set applicable pools directly to maximum; partial percent recovery never rounds down to zero on positive pools.
- Megalixir/Elixir battle messages now explicitly distinguish **full HP at item resolution** from HP reduced by an enemy's later action in the same combat round.
- Portal field-item previews now calculate amounts using the same capped formula as actual item use.
- Regression-checked fixed HP potions, percentage ethers/AP restoratives, all six elemental damage consumables, 30% standard-battle elemental weakness bonuses, Megalixir in mixed HP/MP/AP parties, and inventory debit behavior.
- Refreshed the old item-count regression test for the existing 440-item v1.9.8 catalog (including three Airship materials).
- Remains `1.9.8-airship-expedition`; no item rebalance, database migration, Web rebuild or live state replacement.

## v1.9.8 – Stream Activity / Overlay Hotfix

- Raid `!revive <hero>` now uses shared Raider targeting: @username, Twitch name, or unambiguous character name; Phoenix Down rules and KO checks remain intact.
- World Events support all four `!healparty` tiers; they have independent once-per-player-per-run receipts and a distinct `world_event_party_heal` Gil transaction. No charge on failed attempts.
- Corrected Bot-to-Portal Raid overlay handoff to retain public Raid roster, HP/MP, current effects, queued actions, readiness and rally timers; no private identifiers exposed.
- Active-player Portal status now projects running Hunts, stream battles, Raids, Expeditions, Solo Ventures, and Dungeons with available countdown deadlines.
- Same release identifier: `1.9.8-airship-expedition`. No DB schema migration or gameplay balance change.

## v1.9.8 Stream Mist Party Support — Ventures & Raids

Twitch `!healparty`/`!healparty 1` (100 Gil), `!healparty 2` (250 Gil),
`!healparty 3` (500 Gil), and `!healparty 4` (1,000 Gil) instantly apply
Mist Potion + Mist Ether, Mist Hi-Potion + Mist Ether,
Mist Mega-Potion + Mist Hi-Ether, or Mist X-Potion + Mist Hi-Ether,
respectively, across the **living active Venture or Raid party**.
Each joined player may sponsor one successful use **per Venture and per Raid**;
this resets with the next run. Costs are Gil-only; no owned items are consumed.
Insufficient funds, KO'd actors, unjoined users, full-health/full-MP parties,
and rally-only battles do not spend Gil or consume an allowance. Recovery and
charge are committed together in the persisted runtime state, protecting
restarts and multiple Bot connections. Raid support contributes to the
supporting hero's healing total. No Web changes or schema migration.

# v1.9.8 — Airship Expedition

The Crystal Guild Airship is now the Fellowship's shared unlock for individual remote Expeditions. The old 24–48-hour passive mission **launches are retired**; any mission already in flight can finish and settle using its original persisted rules, and mission history and construction/upgrades remain intact.

- Three Airship-only regions: **The Shattered Sky Isles** (Lv.25+, Crystal Core 0), **The Aetherstorm Expanse** (Lv.35+, Core 1), and **The Forgotten Dominion** (Lv.45+, Core 2). The original five Chocobo regions are unchanged.
- Three new regional bosses and three sky-exclusive salvage materials, with persistent regional exploration, milestones and boss contracts.
- Per-player Airship Expeditions reuse the regular Expedition persistence, routing, combat and rewards; a Chocobo is not required for flying. Multiple members may travel independently.
- Airship upgrades: Hull lowers hazards and improves rescue retention; Engine shortens travel; Cargo increases gathered materials; Survey improves rare-event odds and exploration gains; Crystal Core gates distant regions. Tiers are copied when a flight launches so mid-flight guild upgrades cannot change its conditions.
- Airship-specific events: aerial ambushes, aetherstorms, emergency landings and floating ruins.
- Twitch chat: `!airshipregions`, `!airshipexpedition <region_id> [scout|journey|deep|boss|legendary]`, `!airshipstage`, `!airshiproute [safe|unknown|deep]`, `!airshipcamp`, `!airshipreturn`, `!airshipattack`, `!airshipdefend`, `!airshipretreat`. Existing `!airship` reports Guild construction and unlocked destinations. `!airshipmission` is disabled.
- Portal Expedition Board has separate Chocobo and Guild Airship routes. Fellowship page focuses on upgrades and remote regions, while prior mission history stays visible.
- No database migration required; persistent schema remains **27**, hosted sync schema **1**, Portal Action protocol **39**.
- **v1.9.7 Quick Gear Twitch chat commands remain present** in the full Bot.

**Deployment:** Always back up live Bot/Web databases, volumes and configuration before updating. Merge `Bot/` and `Web/` source patch into the existing tree; keep all image assets and secrets unchanged. Restart Bot, and rebuild Web/frontend through the source-build Dockerfile or normal `npm ci && npm run build`. The static v1.9.7 `frontend/dist` is not a v1.9.8 UI build; do not deploy with `Dockerfile.prebuilt` until the new bundle has been compiled. Do not wipe either database.

---

# v1.9.7 — Queen’s Blood

Queen’s Blood joins Crystal Guild in its own Card Hall, separate from Gold Saucer and Triple Triad.

- **48 illustrated cards:** 16 foundation cards, 16 heroes, and 16 summons and villains. All six approved batches are included, with the final Cactuar, Cloud, Zidane, FFVII Remake Leviathan, and reference-pose Sephiroth revisions. Lightweight 320×480 display copies keep browsing fast; the 1024×1536 lossless originals remain available in the art viewer. Portraits retain their full frame; collection and selected-card views open larger artwork dialogs.
- **Solo progression:** guided tutorial, practice matches, 14 circuit opponents, guaranteed first-win rewards, and three saved 15-card deck slots. Every card can be obtained solo. PvP, raids, and live streams are not progression gates.
- **Live casual invitations:** 10 minutes to accept, 3 minutes for both opening hands, and 90 seconds per turn. Visible turn indicators and a server-based countdown accompany automatic refresh and reconnect handling. Closing the page does not pause a live clock.
- **Correspondence duels:** 48 hours to accept, 24 hours for both opening hands, and 48 hours per turn. Both modes save every action. Missing an opening deadline cancels the game without a result; missing a turn deadline is a forfeit. Live and correspondence records are shown separately.
- **Reliable match state:** deck snapshots at acceptance, private hands, revision checks, duplicate-request protection, authoritative deadlines, and saved-match compatibility.
- **Compact presentation:** dark readable surfaces, illustrated hands and board cards, compact collection rows, full placement/effect previews, and wrapping controls on desktop and mobile.

## Rules and scope

The three-lane territory game uses original Crystal Guild cards and the established Guild rules implementation inspired by Queen’s Blood. Its 15-card decks, opening exchange, turn draws, lane scoring, replacement, destruction, ongoing effects, thresholds, and status-count abilities are explained in the Card Hall’s How to play section. The release does not claim exact conformance to every FFVII Rebirth interaction. Persisted rule identifiers retain their historical names so old matches can still be resumed.

There is no ranked ladder, public matchmaking queue, spectator mode, wagering, or automated defense-deck mode in this release. Live play uses private invitations and periodic state refresh. Timers are enforced by the hosted server; after a restart, overdue turns are settled when the duel is next read or acted on. Both modes need the Portal online; the Bot may be offline.

## Installation and verification

Use `START_HERE.md`. Both service folders and the production frontend are included. No npm rebuild is required when using the prebuilt output. Keep your existing Bot and hosted Web databases and private configuration.

The validation report distinguishes the Queen’s Blood release checks from inherited failures in the historical test suites. Automated game simulations are termination checks, not evidence of human win rates or exhaustive competitive balance. No live deployment or real-player transactions were performed.

### Dungeon Tales & Rest (V2.0.1)
- Ten standard and advanced Dungeon routes now include unique chapter narration and atmospheric room descriptions, snapshotted per run. Existing run saves are unchanged.
- Shared 10-minute per-player Dungeon rest starts after clear, defeat, or retreat. Job Ascension Trials remain exempt.
- The cooldown uses the existing persistent cooldowns table; no schema migration required.
