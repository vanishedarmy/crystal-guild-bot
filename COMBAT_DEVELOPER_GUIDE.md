# Active Battle Editing Guide

Use this file as the first stop when extending Active Battle combat. The design goal is to keep new content declarative and prevent `engine.py` or `twitch_bot.py` from becoming a pile of one-off ability branches.

## 1. File ownership

| File | Edit here for | Do not put here |
|---|---|---|
| `data/active_abilities.json` | ability names, unlock JLv, resource (`mp`/`ap`), cost, target, description, effect list | Python logic |
| `crystal_guild/active_battle.py` | status helpers, target/action parsing helpers, shared primitives | DB writes or Twitch messaging |
| `crystal_guild/engine.py` | encounter state, authoritative resolution, item spending, HP persistence, rewards | timer loops or chat decorators |
| `crystal_guild/encounter_daemon.py` | rally/round deadline advancement and publishing engine messages | damage/status rules |
| `crystal_guild/twitch_bot.py` | thin `!command` adapters | battle math |
| `tests/test_active_battle.py` | Active Battle regression coverage | integration secrets |

## 2. Ability schema

Each Job entry contains `job_id` and three or more abilities:

```json
{
  "id": "power_break",
  "name": "Power Break",
  "level": 1,
  "cost": 4,
  "resource": "ap",
  "target": "enemy",
  "description": "Heavy physical strike that weakens enemy damage for 2 rounds.",
  "effects": [
    {"type": "damage", "scaling": "physical", "power": 1.15},
    {"type": "status", "status": "weaken", "turns": 2, "magnitude": 0.12, "chance": 1.0}
  ]
}
```

Supported target values: `enemy`, `self`, `ally`, `party`.

Supported effect families: `damage`, `heal`, `restore_mp`, `revive`, `status`, `cleanse`, `drain`. The startup data validator rejects unknown effect/target/scaling values.

### Adding an ability that uses existing effects

1. Add/edit only `data/active_abilities.json`.
2. Keep the description player-facing; do not expose internal keys.
3. Run the data validator/self-test.
4. Add a focused behavioral test when the combination is new.
5. Confirm `!abilities <job>` and the Player Guide Job dossier remain understandable.

### Adding a brand-new effect type

1. Define its schema/range validation in `data.py`.
2. Add reusable primitives to `active_battle.py` if needed.
3. Add one authoritative resolution branch in the engine's Active Battle effect resolver.
4. Add tests for success, invalid target, resource spending, and round/status lifetime.
5. Document the effect here and in the Player Guide if players need to reason about it.

## 3. Round invariants

Do not break these without an explicit versioned design change:

- Only living heroes are expected to submit actions.
- One queued action per hero; a new action replaces the old one.
- MP/AP/items are not consumed while merely queued.
- Missing actions default to basic Attack at resolution.
- `encounter_daemon.py` advances time; commands never sleep/wait for a round.
- HP is persisted after rounds so crashes do not revert wounds.
- `_finish_active_encounter()` is the normal single outcome/reward exit.
- All completion paths must clear the active encounter in `finally`/equivalent cleanup.

## 4. Status lifetime

Statuses are dictionaries on the encounter combatant/enemy state. Use `apply_status`, `tick_statuses`, `status_magnitude`, `cleanse`, and `format_statuses` instead of open-coding duration mutation in multiple places.

When adding a status:

1. Give it a player-facing entry in `STATUS_LABELS`.
2. Add it to `HARMFUL_PLAYER_STATUSES` if Remedy/cleanse should remove it.
3. Define exactly when its turns tick.
4. Test both application and expiry.

## 5. Timing / anti-stall

`ENCOUNTER_ROUND_SECONDS` defaults to 20 seconds and is clamped to a minimum of 5. **Timer invariant:** the scheduled deadline never moves earlier because players queue actions. If everyone submits immediately, the round still resolves at its original deadline. If someone does nothing, the round resolves at that same deadline and gives them Attack.

Player-facing commands must never perform an overdue transition. A late `!join`, `!venture`, `!encounter`, or battle action may read/reject state, but only `encounter_daemon.py` (or an explicit owner/admin recovery command) may start or advance timed combat. Chat can wake the daemon only when a *new timer is created* so the scheduler can re-arm itself.

Do not make resolution depend on Twitch message arrival. Network/chat failures should affect presentation, not authoritative battle cleanup.

## 6. Deterministic simulator boundary

`GameEngine._party_battle()` is retained for deterministic balance regression and offline comparison. **Production random encounters do not use it.** New live combat mechanics belong in Active Battle, not in `_party_battle()`.

## 7. Minimum test pass before release

```bash
python -m unittest tests.test_active_battle -v
python -m unittest discover -s tests -v
```

Also validate game data, run Python compilation checks, and exercise at least one mixed-role multi-player encounter through the simulator.

## 8. Enemy combat ownership

Do not add `if monster_id == ...` content branches to the round resolver. Enemy content is intentionally split from engine policy:

| File | Edit here for |
|---|---|
| `data/enemy_profiles.json` | reusable temperament tuning and conditional utility actions |
| `data/enemy_actions.json` | per-monster profile assignment, named skill chance/cooldown/target/effects |
| `crystal_guild/enemy_combat.py` | reusable selection/chance policy only |
| `crystal_guild/engine.py` | generic authoritative application of the selected enemy action |
| `crystal_guild/data.py` | schema/range/coverage validation |
| `tests/test_enemy_combat.py` | enemy-combat regression behavior |

### Adding or tuning an enemy skill

1. Prefer editing `enemy_actions.json`; do not alter the legacy `monsters.json` `special` field merely to change Active Battle.
2. Reuse existing effect/status vocabulary when possible.
3. Keep the skill name/description suitable for player-facing Bestiary/Guide display.
4. Run `GameData.validate()` and `tests.test_enemy_combat`.
5. Test cooldown behavior and at least one low-HP/party-size edge case.

### Adding a new enemy effect family

1. Define validation in `data.py`.
2. Add a reusable resolver path, not a monster-specific branch.
3. Decide explicitly whether the effect belongs to players too; if so, prefer a primitive in `active_battle.py`.
4. Add a deterministic test for selection, application, expiry/resource behavior, and fatal edge cases.
5. Update the Player Guide if the player must reason about it.

**Soft-targeting guardrail:** Active Battle retains the existing Taunt/tank target weighting. Field enemies receive one ordinary action slot per round regardless of rally size; basic and `single` actions choose one living hero, while `party` abilities are the explicit multi-target path. A full threat table, healer prioritization, manual player target selection, or multi-enemy field model should be implemented as a separate versioned system rather than hidden inside enemy skill content.


## Timed Hunts

New Hunts use a persisted per-player assignment layer rather than holding `active_encounter` for minutes or hours:

- `engine.hunt()` validates the mark, snapshots the accepting hero through `_initialize_active_combat()`, stores the snapshot under `active_hunts[player_id]`, starts the mark cooldown, and returns immediately.
- Rank deadlines are fixed by `HUNT_DURATION_SECONDS`: C 15m, B 30m, A 2h, S 5h (S+ currently inherits the S timer until marks are introduced).
- `combat_snapshot()` exposes only the small Hunt deadline rows needed by `EncounterDaemon`.
- `EncounterDaemon._tick_hunts()` calls `engine.resolve_hunt()` only after the assignment deadline and publishes the final result once.
- `resolve_hunt()` temporarily loads the Hunt snapshot into the established field-combat engine, runs rounds internally, then restores any simultaneous shared encounter state.
- `_hunt_auto_action()` is intentionally conservative: urgent healing/cleansing first, a hard per-rank item cap, useful abilities with resource reserve, situational Defend, otherwise Attack.
- `_finish_active_encounter()` remains the authoritative Hunt reward/record persistence path.
- Existing pre-hotfix `active_encounter.kind == "hunt"` checkpoints are still accepted so an in-flight legacy Hunt can finish safely after upgrading.

Do not add long Hunt timers to the global `active_encounter` slot. A player walking away from a Hunt must never block Rally Ventures or the raid scheduler. New Hunt mechanics should continue to reuse the shared combat/status/effect system unless a future release deliberately introduces a separate model.

### Targeting scope

Crystal Guild field battles remain centered on one enemy at a time, so there is intentionally no generalized player-side enemy-selection UI/command system. Enemy-to-player targeting is implicit: ordinary attacks and `single` skills choose one living hero using tank/Taunt weighting, while `party` skills may hit multiple heroes. Ally targeting remains only where support, cleansing, healing, Cover, Raise, or item use requires it.


## Battle Presentation

Battle presentation now has a dedicated pure helper module: `crystal_guild/battle_presentation.py`.

Use it for:

- compact HP/MP/AP/percentage formatting;
- visible status formatting;
- party dashboard packing;
- common round-event shortening;
- bounded round recap formatting.

Do **not** move damage, healing, resource spending, timer checks, reward logic, or status mutation into the presentation module. The resolver should emit understandable event prose first; presentation may shorten that prose after the fact.

`engine._remember_round()` keeps only the latest four resolved rounds in memory. `!battlelog` can also read the most recently completed battle after encounter cleanup. This is intentionally not persisted or synchronized to the hosted Portal.

When adding a new Active Battle mechanic:

1. Implement and test the mechanic at its authoritative engine/data boundary.
2. Make the resolver log the important outcome in plain readable language.
3. Only then add a `compact_event()` pattern if the normal line is too verbose for Twitch.
4. Verify the summary stays bounded and that `+N more` appears when events are omitted.
5. Verify the change does not modify `next_round_at` or daemon ownership.

## Combat editing map

When tuning Active Battle for the current system, use this order:

1. **Individual player ability:** edit `data/active_abilities.json`.
2. **Individual monster skill/profile:** edit `data/enemy_actions.json` or
   `data/enemy_profiles.json`.
3. **Cross-cutting numeric rule:** edit `crystal_guild/balance.py`.
4. **Reusable status/action semantic:** edit `crystal_guild/active_battle.py`.
5. **Authoritative state/persistence boundary:** only then edit `engine.py`.
6. Add/update tests in `tests/test_combat_balance.py` plus the relevant subsystem
   regression file.

### MP / AP tuning

Do not put duplicate resource formulas in `engine.py`, Twitch commands, or Job data. MP and AP pool math belong in `balance.py`; `active_battle.py` exposes the shared pool helpers. Ability `resource` and `cost` remain declarative in `active_abilities.json`, while Defend recovery fractions remain centralized in `balance.py`.

Normal Attack must stay resource-free. Spend MP/AP only when a queued ability actually resolves. Keep compatibility with legacy custom ability catalogs that still use the old numeric `mp` field unless a versioned migration deliberately removes that fallback.

### Status tuning

If a new status can be applied to both heroes and monsters, define what it does
on both sides before shipping it. A label alone is not a mechanic. Keep status
refresh/aging in the shared helpers and keep database persistence out of
encounter-local statuses.

### Stun / hard control

The single-enemy format makes Stun unusually powerful. Successful player Stun
sets `monster_stun_resist_until`; the following round rejects another Stun.
Keep that state ephemeral and encounter-local.

### Hunt resistance

Do not hardcode `if rank == ...` branches in the resolver. Tune the multiplier
tables in `balance.py` and route application through
`active_hunt_status_chance()`.
