# Crystal Guild — V2.11 Beastmaster Bond Growth + Portal Review

**Source baseline:** v1.9.97.7 regional-progression, V2.10 Bot candidate. This is an integration candidate, not a live release.

## Implemented in the real Python Bot

- Existing five-slot owned companion roster and selection are preserved. Species level is unchanged; **Bond rank** is a separate 1–20 progression.
- A verified, successful damaging `call_beast` or `king_of_beasts` action records a pet assist in the server-side combat snapshot (active field combat and raid).
- When the team wins a shared field encounter or raid, an owned companion that assisted receives **Bond XP = min(200, max(20, 20 + enemy level × 2))**.
- Rewards are committed in the same SQLite player reward transaction, with a unique `(event_key, player_id)` receipt; replaying the same victory does not repeat pet XP.
- Bond level uses cumulative threshold `25 * (rank - 1)^2`. Maximum Bond rank is 20 (9,025 total XP).
- Verified combat snapshots include the pet's Bond rank; the owned companion's assist damage bonus increases gently with rank, capped at **12%** before Relic multipliers.
- `!pets` includes Bond rank. `!tame`, `!petselect`, `!petrelease` continue to work and ownership persists.
- Database migration **29→30** adds `bond_xp`, `bond_assists`, and `beastmaster_bond_receipts`. Existing players, Bestiary, companion ownership and selection are preserved, with a pre-migration backup.
- Portal `overview.companions` includes owned slots and sanitized per-pet rank, progress, damage bonus and activity count. No player ID is included.

## Merge-ready Web patch

- `Web/frontend/src/player/Overview.jsx` displays a companion roster and Bond XP progress from the Bot's existing Portal overview snapshot.
- Includes the previously prepared Item Encyclopedia / Relic UI compatibility display files to expose Unique/Exotic rarity and gear/Relic effect descriptions.
- All Web changes are source files only; full Vite build and deployed integration have **not** been run.

## Important boundaries

- Bond XP currently awards for successful pet participation in **shared field encounter victory** (venture, world event and shared active loop) and **raid victory**. It does **not** yet award from separate solo/dungeon/expedition or personal-hunt reward paths.
- Replaying a completed pet receipt does not award pet XP again. Other pre-existing reward processing outside this feature is not altered.
- Pets remain assist modifiers; this is not independent pet AI, pet HP, pet turns, pet skill training, or on-demand free XP.
- The base monster species level and every existing Relic/gear ID, quest and balance definition remain unchanged. Pet growth applies only with a verified owned companion.
- The Web is read-only for pet management; Twitch commands continue to manage the roster.

## Validation

- 10 new V2.11 tests passed (field and raid ability recording, winning field reward integration, receipts, rollback, migration-compatible schema, restarting, Portals).
- 106 selected prior Bot regression tests passed (V2.10/V2.7–V2.9 Relic, active battles, enemy combat, Portal snapshot and raid healing).
- 7 Web Item/Relic presentation tests passed, 4 changed frontend files parsed as valid JavaScript/JSX.
- Real file-backed V2.10 schema-29 → V2.11 schema-30 migration smoke passed and created a verified backup.
- **Not validated:** entire project suite, Vite production build, deployed Bot/Portal sync, personal-hunt/solo/dungeon awarding.

## Installation (candidate)

1. Back up the live Bot, config, and SQLite database before any replacement. Database migrations are not reversible automatically.
2. Choose either full `Bot/` ZIP **or** V2.11-only Bot merge ZIP, never both. Both retain original `.env` policy (no secrets included).
3. Start the updated Bot against a non-production copy of the real database first and verify schema 30 and pet roster preservation.
4. Merge the Web ZIP's `Web/` tree into the matching v1.9.97.7 Web source (approved artwork Batches 01–15 assumed) and run `npm ci && npm run build` in `Web/frontend` on your own installation.
5. Verify companion roster/XP and item effects in an authenticated Portal session; then test battles and Twitch actions before production promotion.
