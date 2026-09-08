# Crystal Guild — Game Design

## Core loop

Crystal Guild is a persistent Final Fantasy-inspired Twitch chat RPG. Viewers recruit a hero, choose Jobs, venture into encounters, complete Hunts and raids, collect equipment/materials, unlock Jobs and Masteries, forge gear, complete Relics, and build long-term records/achievements.

## Progression

- Character Level represents account-wide hero growth.
- Job Level/JP represents current Job development.
- Jobs define stat growth, passive milestones, active abilities, and resource type.
- Masteries provide cross-Job passive customization.
- Equipment is level- and class/job-gated; progression provides regular upgrade opportunities through Lv.50.

## Combat

- Ventures and Hunts use autonomous timed rounds.
- Basic Attack is always available and resource-free.
- Magical abilities spend persistent MP.
- Martial/physical abilities spend persistent AP.
- Defend trades an action for mitigation and resource recovery.
- Enemy actions/statuses are data-driven.
- Field battles intentionally focus on one primary enemy; support abilities may target allies/party.
- Field enemies use soft targeting: one ordinary enemy action per round selects one living hero, weighted toward tanks/Taunt; only explicit party skills may hit multiple heroes.
- Stream/Rally Ventures resolve as 100% ENCOUNTER events; the Rally treasure branch is removed. Portal Solo Venture retains its separate 80% ENCOUNTER / 20% TREASURE stage roll.
- Venture ENCOUNTER monster rolls are capped at 10 levels above the initiating hero.
- Treasure outcomes are reserved for Portal Solo Venture; Stream/Rally Ventures always open a shared encounter.
- Raids use timed community participation and role-aware contribution/reward rules.

## Economy

- Gil is the general currency. Hunt Seals support Hunt/relic progression.
- Daily income, resale ratios, crafting/forge costs, repeated Hunt rewards, and raid pools are bounded to avoid runaway inflation/arbitrage.
- Transaction history supports diagnostics through the Streamer Dashboard and owner economy tools.

## Equipment and crafting

- Items are categorized as Weapons, Armor, Items, or Materials for player-facing inventory navigation.
- Equipment has minimum-level and class/job compatibility rules.
- Crafting consumes materials; forge upgrades provide long-term gear sinks.
- Relic weapons are long-form endgame progression rather than ordinary shop replacements.

## Persistence and reliability

- The local Bot database is authoritative.
- Player progression survives restart and compatible 1.x upgrades.
- Live combat has a small recovery checkpoint; progression and checkpoint writes are transactionally coordinated.
- The hosted Portal receives only sanitized snapshots.

## Player-facing Web

- Adventurer Portal lists public heroes.
- Player profiles expose sanitized progression, equipment, records, HP and applicable MP/AP.
- Player Guide is the canonical browsable mechanics/command reference.
- Streamer Dashboard is read-only operational/reference UI.
- Privacy Policy and sync status are available from the Web Hub.

## Design guardrails

- Preserve player data across 1.x updates unless a tested migration is unavoidable.
- Prefer declarative data over one-off engine branches.
- Keep chat commands thin; authoritative timers/resolution live in the scheduler/engine.
- Do not add generalized multi-enemy target selection until the encounter model actually needs it.
- New economy sources should ship with matching sinks or bounded budgets.
- Public Web features must not gain authoritative write access to local progression.
